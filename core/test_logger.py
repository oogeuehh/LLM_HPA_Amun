from blocker_logger import ExperimentLogger
import time

logger = ExperimentLogger("logs/test_experiment.log")

logger.log_transition(
    connection_id="test_conn_1",
    src=None,
    dst="ls",
    Pr_Actual=0.5,
    Pr_Max=0.8,
    payoff=1.0,
    block=False,
    commands_raw="ls"
)

time.sleep(1)

logger.log_transition(
    connection_id="test_conn_1",
    src="ls",
    dst="cat /etc/passwd",
    Pr_Actual=0.3,
    Pr_Max=0.7,
    payoff=2.0,
    block=True,
    commands_raw="cat /etc/passwd"
)

print("✅ Logger test finished. Check logs/test_experiment.log")
