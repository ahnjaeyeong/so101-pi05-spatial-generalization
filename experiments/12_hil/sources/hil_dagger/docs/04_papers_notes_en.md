# HIL correction methods: RaC, IWR, HG-DAgger (+ Sirius note)

Legend: [P] = stated in paper (quote or close paraphrase), [I] = my inference, [NS] = not stated.
Retrieved 2026-11-04. RaC from arXiv HTML v1 (https://arxiv.org/html/2509.07953). IWR from the arXiv PDF v1 (https://arxiv.org/pdf/2012.06733, the only version) converted with pdftotext. HG-DAgger from https://arxiv.org/pdf/1810.02890. Sirius from https://arxiv.org/pdf/2211.08416.

---

## 1. RaC: Robot Learning for Long-Horizon Tasks by Scaling Recovery and Correction (Hu et al., CMU, arXiv 2509.07953)

### Definitions (Sec. 4.1)
- [P] **Recovery**: the human actions starting at intervention state s_t form a recovery segment if the state they reach "lies within the distribution of states visited in the prefix of human demonstrations". In other words, they go back to a familiar earlier-phase state.
- [P] **Correction**: the segment is corrective if the state it reaches lies within the distribution of demo states visited *after* timestep t. Correction pushes the task forward.
- [P] Recovery "returns the policy to familiar previous states", while correction "show[s] how to push the trajectory forward".

### Triggering and handover (Abstract, Sec. 1, 4.2, 4.3)
- [P] The human decides when to intervene: operators "intervene when failure appears imminent" and take over "as soon as it begins to deviate from the expected course". There is no automated trigger.
- [P] Device: Oculus Quest VR controllers with a **clutch**. While the side button is held, "controller motions are mapped directly to the end effector". When it is released, the robot follows the learned policy. Relative pose deltas in a local frame remove the need for global pose alignment.
- [NS] Whether the robot pauses or holds still at handover.
- [NS] How intervention interacts with action chunks. [P] Algorithm 1 chooses human or policy per step.
- [P] Operator aid: a SAM2-derived heatmap of gripper visitation from the initial demos is overlaid on the operator display to show "in-distribution regions where the robot grippers should recover back to upon intervention" (Sec. 4.3, Fig. 5). Appendix B captions mention "driving the gripper backwards".
- [NS] Detailed recovery instructions such as reopening the gripper, returning to pre-grasp, or a set duration.

### Operator rules (Sec. 4.2)
- [P] **Rule 1**: "Pair each recovery segment with a correction segment." The operator first recovers to an in-distribution state, then corrects.
- [P] **Rule 2**: "After an intervention concludes, we terminate the entire episode." The stated rationale is that continuing would "contaminate later sub-tasks with a distribution of states" that is off-distribution.

### Data selection and labelling (Sec. 4.4, Algorithm 1)
- [P] Only human-intervention transitions (is_human=1) are added from intervened episodes: "add only human intervention transitions into dataset". Section 4.4 says "we do not include any transitions from the robot's own rollouts, unless the trajectory reaches full task completion without any human intervention".
- [P] Fully autonomous successful episodes are added in full, "with no human budget counted".
- [P] Pre-intervention policy frames are therefore **discarded**, but the budget still charges the "full episode length".
- [P/I] Recovery and correction come from the same intervention in one episode, and the episode ends afterwards. The stored flag is only binary is_human. Recovery and correction are not separately tagged at collection time. [P] They are classified post hoc only for analysis in Sec. 5.4 ("We classify each intervention frame as either a recovery segment or a corrective segment"), and the paper does not say how.
- [NS] Loss masking or weighting. No weighting is described; the method is plain BC on the aggregated dataset.

### Training recipe (Algorithm 1, Sec. 4.4, App. A Table 2)
- [P] Round 0 is full demos with budget R0. Then come K alternating rounds of intervention and training, with Train(D_{0:K}) on the aggregated data each round.
- [P] K = 6 (shirt-hanging), 10 (lid-sealing), 9 (takeout-box). The simulation ablation uses 4 rounds.
- [P] AdamW, constant LR 1e-4, global batch 512, 200 epochs.
- [NS] From scratch vs fine-tuning from the previous checkpoint. [NS] Base:RaC data ratio. [NS] Per-round episode or hour counts. [NS] Number of demos in round 0 per task.

### Architecture (Sec. 4.4, App. A)
- [P] MM-DiT with about 300M parameters in the text; Table 3 says 367.865M. It uses conditional flow matching with 10 Euler steps.
- [P] Three cameras (one top, two wrist), each with a ResNet-50 encoder (ResNet-18 in sim), plus a proprio token.
- [P] Action chunk H = 60 (1 s at 60 Hz). Inference runs every 0.5 s and executes the first half of the chunk. Action dim is 14 (bimanual).
- [P] Hardware: 2× xArm-7 with soft grippers.
- [P] This is **not a VLA**. It is trained on task data, and VLA integration is listed as future work.

### Results (Sec. 5.2–5.4)
- [P] Table 1, shirt-hanging:

  | Method | Params | Data | Success |
  |---|---|---|---|
  | RaC | 368M | 5 h | 78.3% |
  | ALOHA Unleashed | 217M | ~89 h | 75.0% |
  | Seed GR-3 | 4B | 116 h | ~63.6% (estimated) |

- [P] The headline claim is "10× less data". RaC gives "at least a 2× improvement in data efficiency" over batched full-demo collection and "consistently outperforms HG-DAgger". These comparisons were run on shirt-hanging only.
- [P] Evaluation used 60 trials per real task and 100 in sim.
- [NS in text] Success numbers for lid-sealing and takeout-box. Those appear only in Fig. 8 and were not extracted.
- [P] Fig. 10 reports a "strong linear scaling relationship" between the number of recovery segments in rollouts and success. RaC rollouts are longer (Fig. 11).
- [P] Fig. 12 (sim): RaC data has a recovery:correction ratio of about 1:1 to 1:2. Conventional intervention data is about 1:3 and 1:10.
- [P] Ablation (Sec. 5.4): "terminating early after an intervention alone ("Ours w/o Rule 1") yields more effective performance scaling" than continuing the rollout.
- [P] The text is inconsistent about which variant equals HG-DAgger: it says "w/o Rule 1" in one place and "w/o Rule 1&2" in another.

### Limitations (Sec. 6, no dedicated section)
- [P] Applying RaC to VLAs is untested: "unclear if such behaviors systematically emerge in most settings or not".
- [P] Online RL fine-tuning is future work.
- [I] Cross-paper comparisons use different robots and an estimated GR-3 number.

### SO-101 note (one line)
- [I] The protocol (clutch handover, recover→correct, terminate, keep only human frames) maps onto leader/follower teleop, but RaC's model is a from-scratch 300M MM-DiT, not a pretrained VLA.

---

## 2. IWR: Human-in-the-Loop Imitation Learning using Remote Teleoperation (Mandlekar, Xu, Martín-Martín, Zhu, Fei-Fei, Savarese; arXiv 2012.06733 v1, Dec 2020)

### Data collection (Sec. IV-A)
- [P] Built on RoboTurk. The operator watches a browser video stream. They "pause and resume policy execution by tapping a button on their smartphone". They "intervene by holding another button down and moving their phone", which applies relative pose commands.
- [P] The human "moves the robot arm into a state where the policy is likely to succeed, and then returns control to the policy" (Fig. 1 caption). The episode **continues** after the intervention, unlike RaC.
- [P] "We record each completed task demonstration with binary intervention labels".
- [P] Experiments are **simulation only** (MuJoCo/robosuite, Sawyer with OSC). The footnote says real arms were inaccessible due to COVID.

### Weighting rule (Sec. IV-C)
- [P] The data splits into D_I (human intervention samples) and D_R (on-policy robot samples). The target distribution is q(s,a) ∝ α·ρ_I(s,a) + ρ_R(s,a).
- [P] The paper sets "α = |D_R|/|D_I| so that q(s,a) samples from ρ_I and ρ_R in equal proportion". This is equivalent to θ = argmin ‖π(s_I)−a_I‖² + ‖π(s_R)−a_R‖², with each term drawn from its own dataset. In practice, each batch has equal-size sub-batches from D_I and D_R (Fig. 3).
- [P] D_R holds all non-intervention samples. Based on the IWR-NB baseline wording and Sirius's critique, this includes the initial full demos, so demos get down-weighted relative to their natural share.
- [P] Rationale: on-policy samples act as regularization "that keeps the policy close to previous policy iterates". HG-DAgger-style discarding "can cause the policy trained in the next round to change substantially … due to covariate shift".
- [P] **Nothing is discarded** in IWR, including the robot samples right before an intervention. The project site also does not mention discarding.
- [P, Sirius] The pre-intervention discard comes from **Sirius** (Liu et al., RSS 2023, Sec. IV-B/D), not IWR. Sirius uses four classes: demo, intv, robot, and preintv, where preintv is the ℓ = 15 steps before each intervention, based on about 2 s of human reaction time. Each sample gets weight w = P*(c)/P(c), with these targets:
  - P*(intv) = 0.5, "adapted from prior work [IWR]"
  - P*(preintv) = 0
  - P*(demo) = P(demo), kept at its natural share
  - robot takes the remainder

  Sirius uses BC-RNN with a GMM head.

### Protocol and model (Sec. V-C)
- [P] Each operator started from 30 demos and a base policy, then ran 3 additional rounds.
- [P] Each round collected until intervention samples reached about 33% of the initial dataset's samples.
- [P] After each round, the next policy is trained "for a fixed number of epochs". [NS] Fine-tune vs retrain from scratch.
- [P] Policy: 2-layer LSTM with hidden size 100, sequence length 10, Adam (this is BC-RNN-style). It uses low-dimensional observations (poses), not images. There is no action chunking.
- [P] Evaluation: 50 rollouts per checkpoint and 3 seeds. Each reported number is the max over checkpoints of the average success.

### Baselines and numbers (Tables I–IV)
- [P] Baselines:
  - **IWR-NB**: same data as IWR but one dataset with uniform sampling.
  - **HG-DAgger**: keeps only intervention samples.
  - **Full Demos**: same number of samples as full demonstrations.
  - **Base**: the 30-demo policy.
- [P] Threading, single operator (Table I):

  | Method | Round 1 | Round 2 | Final |
  |---|---|---|---|
  | Base | – | – | 58.0 |
  | Full Demos | – | – | 76.7 |
  | HG-DAgger | 57.3 | 62.7 | 75.3 |
  | IWR-NB | 76.0 | 72.0 | 74.7 |
  | **IWR** | 84.0 | 90.7 | **87.3** |

- [P] Coffee Machine, 3 operators (Table II):

  | Method | Round 1 | Round 2 | Final |
  |---|---|---|---|
  | Base | – | – | 52.0 |
  | Full Demos | – | – | 64.9 |
  | HG-DAgger | 70.2 | 71.1 | 69.6 |
  | **IWR** | 79.6 | 79.5 | **87.5** |

- [P] Cross-dataset (Tables III/IV): IWR training on the other methods' final datasets reaches 84.7–87.3 (Threading) and 85.6 (Coffee). The authors conclude the gain comes from how the data is used, not only from data quality.
- [P] A single large Round 1 with the same total intervention samples showed no significant difference on Threading and was about 7% lower on Coffee. This suggests iteration matters more for longer, multi-bottleneck tasks.

### Limitations
- [P] There is no limitations section. Only simulation was tested, with low-dimensional states. Real robots are listed as future work.
- [I] The equal 50/50 split ignores intervention length and quality. Robot samples just before interventions, which are likely bad, stay in D_R. Sirius explicitly fixes this.

### SO-101 note (one line)
- [I] IWR's 50/50 per-batch balance is easy to apply as a sampler over a per-frame is_intervention flag. Its evidence, though, comes from a small LSTM in simulation, not a VLA.

---

## 3. HG-DAgger (Kelly, Sidrane, Driggs-Campbell, Kochenderfer; arXiv 1810.02890, ICRA 2019)

- [P] Sec. II: the human expert is the gating function. The novice runs "until the expert observes that the novice has entered an unsafe region". The expert takes over with uninterrupted control, "guides the system back to a safe and stable region", and then returns control to the novice. The episode continues.
- [P] **Only expert-controlled samples are labelled and kept**: D_i = {(O(x_t), π_H(x_t)) | g(x_t)=1}. "Expert action labels are only collected and added to D during these recovery trajectories". Novice samples are discarded.
- [P] D is initialized with BC demos D_BC. Each epoch aggregates D ← D ∪ D_j and trains π_{N,i+1} on D. There is no weighting.
- [P] Extra: the novice is an ensemble. Its "doubt" (‖diag of ensemble covariance‖₂) at each takeover is logged, and the threshold τ is the mean of the last 25% of logged doubts. τ is used for risk assessment only, not for gating at training time.
- [P] Domain: autonomous driving, both simulation and a real test vehicle.
- [I] Positioning: a strategy that saves only operator-controlled frames, aggregates them with the base data, and trains plain BC is HG-DAgger. RaC adds recover-then-correct and stopping the episode after intervention. IWR keeps the policy frames too and uses 50/50 batch balancing. Sirius additionally drops the about 15 pre-intervention steps and keeps demos at their natural ratio.
