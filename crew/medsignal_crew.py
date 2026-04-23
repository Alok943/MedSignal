import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeout
from typing import Tuple, Optional, List

from agents.ddx_agent import get_ddx_agent, run_ddx, DDxOutput
from agents.red_flag_agent import run_red_flags, RedFlagOutput, RedFlagItem, _apply_consistency_adjustment
from agents.consistency_agent import run_consistency, ConsistencyOutput
from agents.summary_agent import run_summary, FinalReport
from tools.rule_engine import run_hard_rules, RuleMatch
from tools.openfda_tool import check_all_interactions, DrugInteractionResult

from typing import Literal, cast


# Add this helper at top of orchestrator
Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]

def _validate_severity(s: str) -> Severity:
    """Cast string to Severity literal with validation."""
    valid = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
    if s not in valid:
        return "LOW" # safe default
    return cast(Severity, s)

logger = logging.getLogger(__name__)


def _run_ddx_worker(llm, structured_data: dict) -> DDxOutput:
    agent = get_ddx_agent(llm)
    return run_ddx(agent, structured_data)

def _run_red_flag_worker(
    llm,
    structured_data: dict,
    rule_matches: List[RuleMatch],
    fda_interactions: List[DrugInteractionResult],
    consistency_result: ConsistencyOutput
) -> RedFlagOutput:
    return run_red_flags(
        llm,
        structured_data,
        rule_matches,
        fda_interactions,
        consistency_result
    )

def _run_consistency_worker(llm, structured_data: dict) -> ConsistencyOutput:
    return run_consistency(llm, structured_data)

def run_pre_analysis(structured_data: dict) -> Tuple[List[RuleMatch], List[DrugInteractionResult]]:
    logger.debug("Running hard rules...")
    rule_matches = run_hard_rules(structured_data)
    logger.debug(f"Rules triggered: {len(rule_matches)}")

    logger.debug("Checking OpenFDA...")
    medications = structured_data.get("medications", [])
    fda_interactions = check_all_interactions(medications) # FIXED
    logger.debug(f"FDA interactions found: {len(fda_interactions)}")

    return rule_matches, fda_interactions

def run_medsignal_crew(llm, structured_data: dict) -> FinalReport:
    # Stage 1: Pre-analysis
    rule_matches, fda_interactions = run_pre_analysis(structured_data)

    # Stage 2: Consistency FIRST
    logger.debug("Running consistency agent...")
    consistency_result = _run_consistency_worker(llm, structured_data)

    # Stage 3: Parallel execution
    logger.debug("Starting parallel agent execution...")
    ddx_result: Optional[DDxOutput] = None
    red_flag_result: Optional[RedFlagOutput] = None

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(_run_ddx_worker, llm, structured_data): "ddx",
            executor.submit(
                _run_red_flag_worker,
                llm,
                structured_data,
                rule_matches,
                fda_interactions,
                consistency_result
            ): "red_flag",
        }

        try:
            for future in as_completed(futures, timeout=15): # FIXED: added timeout
                label = futures[future]
                try:
                    result = future.result(timeout=14)
                    if label == "ddx":
                        ddx_result = result
                    elif label == "red_flag":
                        red_flag_result = result
                except Exception as e:
                    logger.error(f"{label} agent failed: {e}")
        except FutureTimeout:
            logger.error("Parallel execution timed out")

        # Fallbacks
        if ddx_result is None:
            from agents.ddx_agent import DifferentialItem
            ddx_result = DDxOutput(
                differential=[DifferentialItem(
                    rank=1, condition="Unknown — DDx agent failed",
                    severity="HIGH", probability="LOW", reasoning="agent error"
                )],
                ddx_confidence="LOW",
                ddx_notes="DDx agent encountered an error",
                missing_critical_data=[]
            )

        if red_flag_result is None:
            prefilled = [
                RedFlagItem(
                    severity=cast(Severity, m.severity),
                    flag=m.flag,
                    reasoning=m.reasoning,
                    source="RULE",
                    confidence=m.confidence # FIXED: use actual
                )
                for m in rule_matches
            ]
            # FIXED: compute actual max severity
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            sev = min(
                (m.severity for m in rule_matches),
                key=lambda s: severity_order.get(s, 4),
                default="LOW"
            )
            red_flag_result = RedFlagOutput(
                red_flags=prefilled,
                overall_severity=cast(Severity, sev),
                llm_flags_added=0,
                fda_confirmed_count=0
            )
            # FIXED: apply consistency even in fallback
            red_flag_result = _apply_consistency_adjustment(
                red_flag_result, consistency_result
            )

    # Stage 4: Summary
    logger.debug("Running summary agent...")
    final_report = run_summary(
        llm, structured_data, ddx_result, red_flag_result, consistency_result
    )

    logger.debug(f"Pipeline complete. Final severity: {final_report.severity}")
    return final_report