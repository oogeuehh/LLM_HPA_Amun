# -*- coding: utf-8 -*-
import pandas as pd
from core.blocker import Blocker
from core.input_manager import split_commands
import os

def run_online_test(csv_path, log_path="logs/advanced_online_test.log"):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    # 打开日志文件，追加模式
    log_file = open(log_path, "a", encoding="utf-8")

    def log_print(*args, **kwargs):
        """同时打印到终端和写入日志文件"""
        print(*args, **kwargs)
        print(*args, **kwargs, file=log_file)
        log_file.flush()  # 立即写入

    log_print("\n===== START ONLINE TEST =====")
    blocker = Blocker(
        counts_file="core/transition_counts_matrix.csv",
        probs_file="core/transition_probabilities_matrix.csv"
    )

    df = pd.read_csv(csv_path)
    if "input" not in df.columns:
        raise ValueError("CSV 文件中必须包含 'input' 列！")

    total_transitions = 0
    blocked_transitions = 0

    for idx, cmd in enumerate(df["input"]):
        parsed = split_commands(cmd)
        log_print(f"\n[ROW {idx}] raw: {cmd}")
        log_print(f"[ROW {idx}] parsed: {parsed}")

        for p in parsed:
            src = blocker.matrix.last_command
            decision = blocker.check_and_update(p)
            blocker.matrix.update_matrix(src, p, save=False)

            total_transitions += 1
            if decision["block"]:
                blocked_transitions += 1

            log_print(f"[TRANSITION] src={src}, dst={p}, "
                      f"Pr_Actual={decision['Pr_Actual']}, Pr_Max={decision['Pr_Max']}, "
                      f"payoff={decision['payoff']:.3f}, block={decision['block']}")

    # 所有更新完成后再保存一次
    blocker.matrix.save_matrix()

    block_rate = blocked_transitions / total_transitions if total_transitions > 0 else 0.0

    log_print("\n===== END ONLINE TEST =====")
    log_print(f"\n[TOTAL TRANSITIONS]: {total_transitions}")
    log_print(f"[BLOCKED TRANSITIONS]: {blocked_transitions}")
    log_print(f"[BLOCK RATE]: {block_rate:.3%}")

    log_file.close()


if __name__ == "__main__":
    run_online_test("core/parsed_cowrie_test_commands.csv")

# # -*- coding: utf-8 -*-
# import pandas as pd
# from core.blocker import Blocker
# from core.input_manager import split_commands
# import os
# from collections import defaultdict

# def run_session_block_test(csv_path, log_path="logs/advanced_online_test.log", thresholds=None):
#     os.makedirs(os.path.dirname(log_path), exist_ok=True)
#     log_file = open(log_path, "w", encoding="utf-8")  # 每次覆盖日志

#     def log_print(*args, **kwargs):
#         print(*args, **kwargs)
#         print(*args, **kwargs, file=log_file)
#         log_file.flush()

#     if thresholds is None:
#         thresholds = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]

#     df = pd.read_csv(csv_path)
#     if not {"session", "input"}.issubset(df.columns):
#         raise ValueError("CSV 文件中必须包含 'session' 和 'input' 列！")

#     # 按 session 分组
#     sessions = df.groupby("session")["input"].apply(list).to_dict()

#     # 获取训练集命令集合，用于 unseen 判断
#     # 如果你希望用独立训练集，可以在这里加载
#     train_set = set()  # 或者从 csv 加载训练集 input 列
#     unique_unseen_if_no_block = set()
#     for session_inputs in sessions.values():
#         for cmd in session_inputs:
#             parsed = split_commands(cmd)
#             unique_unseen_if_no_block.update([p for p in parsed if p not in train_set])

#     results = []

#     # 阈值扫描
#     for B in thresholds:
#         log_print(f"\n===== THRESHOLD={B} =====")
#         blocker = Blocker(
#             counts_file="core/transition_counts_matrix.csv",
#             probs_file="core/transition_probabilities_matrix.csv"
#         )

#         total_sessions = len(sessions)
#         blocked_sessions = 0
#         transitions_before_block_list = []
#         unseen_collected = set()
#         unseen_per_blocked_session = []

#         for sid, session_inputs in sessions.items():
#             session_blocked = False
#             transitions_count = 0
#             session_unseen = set()

#             for cmd in session_inputs:
#                 parsed = split_commands(cmd)
#                 for p in parsed:
#                     src = blocker.matrix.last_command
#                     decision = blocker.check_and_update(p)
#                     # 阈值判断
#                     if decision["payoff"] >= B and not session_blocked:
#                         session_blocked = True
#                         blocked_sessions += 1
#                         transitions_before_block_list.append(transitions_count+1)
#                         unseen_collected.update(session_unseen)
#                         unseen_per_blocked_session.append(len(session_unseen))
#                         # 假设 block 后 session 停止
#                         break

#                     # 收集 unseen
#                     if p not in train_set:
#                         session_unseen.add(p)

#                     transitions_count += 1

#                 if session_blocked:
#                     break

#         # 如果 session 永不 block，补充未被 block 的 unseen
#         for sid, session_inputs in sessions.items():
#             session_unseen = set()
#             for cmd in session_inputs:
#                 parsed = split_commands(cmd)
#                 for p in parsed:
#                     if p not in train_set:
#                         session_unseen.add(p)
#             unseen_collected.update(session_unseen)

#         # 统计指标
#         sessions_blocked_frac = blocked_sessions / total_sessions if total_sessions > 0 else 0.0
#         avg_transitions_before_block = (sum(transitions_before_block_list)/len(transitions_before_block_list)
#                                         if transitions_before_block_list else 0.0)
#         unique_unseen_before_block = len(unseen_collected)
#         unique_unseen_total = len(unique_unseen_if_no_block)
#         avg_unseen_per_blocked_session = (sum(unseen_per_blocked_session)/len(unseen_per_blocked_session)
#                                           if unseen_per_blocked_session else 0.0)

#         results.append({
#             "threshold": B,
#             "sessions_blocked_frac": sessions_blocked_frac,
#             "avg_transitions_before_block": avg_transitions_before_block,
#             "unique_unseen_before_block": unique_unseen_before_block,
#             "unique_unseen_if_no_block": unique_unseen_total,
#             "avg_unseen_per_blocked_session": avg_unseen_per_blocked_session
#         })

#         log_print(f"[RESULT] Threshold={B}: blocked_sessions_frac={sessions_blocked_frac:.3f}, "
#                   f"avg_transitions_before_block={avg_transitions_before_block:.2f}, "
#                   f"unique_unseen_before_block={unique_unseen_before_block}, "
#                   f"unique_unseen_if_no_block={unique_unseen_total}, "
#                   f"avg_unseen_per_blocked_session={avg_unseen_per_blocked_session:.2f}")

#     log_file.close()
#     return pd.DataFrame(results)


# if __name__ == "__main__":
#     df_results = run_session_block_test("core/parsed_cowrie_test_commands.csv")
#     print(df_results)

