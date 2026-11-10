# 가짜 장치 e2e 결과 (check_results.py 자동 생성)

| 시나리오 | 검사 통과 | 예외 |
|---|---|---|
| S10_adapter_start_paused_reset | 15/15 | - |
| S11_adapter_fast_correction | 15/15 | - |
| S12_adapter_rtc_fault | 16/16 | - |
| S13_adapter_leader_fault | 13/13 | ['ConnectionError: fake leader: injected read failure'] |
| S14_adapter_follower_fault | 13/13 | ['ConnectionError: fake follower: injected write failure'] |
| S15_adapter_normal_end_home | 12/12 | - |
| S16_adapter_pty_keys | 13/13 | - |
| S17_adapter_viewer_killed | 13/13 | - |
| S18_adapter_tap_fault | 13/13 | - |
| S1_normal | 7/7 | - |
| S2_key_race | 7/7 | - |
| S3_esc_in_correction | 7/7 | - |
| S4_leader_fault | 7/7 | ['ConnectionError: fake leader: injected read failure'] |
| S5_rtc_fault | 7/7 | - |
| S6a_enable_stale | 7/7 | - |
| S6b_enable_present | 7/7 | - |
| S7_adapter_normal | 13/13 | - |
| S8_adapter_esc_in_correction | 13/13 | - |
| S9_follower_write_fault | 7/7 | ['ConnectionError: fake follower: injected write failure'] |
