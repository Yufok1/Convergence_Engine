# Convergence Engine Crypto Whitepaper (Draft)

## Purpose and Scope
This whitepaper proposes how Convergence Engine can incorporate crypto-native functionality in a responsible, utility-first way. It covers protocol roles, on/off-chain boundaries, token design options, security and compliance guardrails, economic flows, data integrity, governance, and phased rollout. The goal is to enable verifiable competition, coordination, and rewards without compromising the core agent ecosystem.

## Design Principles
- Utility before speculation: prioritize in-product usefulness (access, staking, reputation) over price dynamics.
- Progressive decentralization: ship centrally-orchestrated MVPs, then open critical surfaces gradually.
- Security first: minimal on-chain complexity; favor well-audited primitives; defense-in-depth.
- User choice: non-custodial by default; custodial/enterprise paths for regulated contexts.
- Observability: transparent metrics for fairness, integrity, and economic health.

## System Roles
- Player: runs an agent client (CocoonLink) to battle, collaborate, and trade.
- Operator: runs CocoonHatch relay nodes to broker matches and messages.
- Curator/Trainer: provides model updates, training data, and evaluation suites.
- Governor: holds governance/stewardship power (token-weighted, reputation-weighted, or hybrid).
- Auditor/Oracle: attests to off-chain events (match results, randomness, checkpoints).

## On-Chain vs Off-Chain Boundaries
- Off-chain (fast loop): agent inference, battles, training, replay storage, P2P messaging.
- On-chain (slow loop): settlements, staking, reputational commitments, reward distribution, buy-ins, escrow, dispute bonds, oracle attestations, randomness beacons.
- Hybrid: hashes/commitments of game state snapshots anchored on-chain for integrity proofs; zk proofs optional later.

## Token Options
- Single-token model (Utility/Governance Hybrid): one token used for staking, access, rewards, and governance. Simpler liquidity and UX; risk of role overload.
- Dual-token model:
  - Utility token: used for access fees, buy-ins, rewards, and staking for fairness.
  - Governance token: used for protocol upgrades, parameter votes, council elections. Can be non-transferable or have slow-transfer windows to reduce governance capture.
- Reputation token (non-transferable): earned via verifiable participation and performance; used to gate tournaments, grants, and governance weight.
- Stable unit alignment: denominate payouts and fees in stablecoins to reduce volatility while retaining governance/reputation tokens for control and access.

## Core Crypto Mechanics
- Staking for Fair Play: operators and players stake to participate; slashed on provable fraud or disconnect abuse.
- Buy-ins and Prize Pools: tournaments and ladders collect entry fees; payouts triggered by oracle-verified results.
- Match Settlement: CocoonHatch produces signed results; Oracles relay to chain; smart contracts release prizes and update reputations.
- Breeding/Forging: combine agents/artifacts with on-chain recipes and off-chain computation; mint resultant metadata on-chain with off-chain weights and proofs of origin.
- Marketplace: listings escrowed on-chain; artifacts and agent licenses represented as NFTs or soulbound licenses; delivery of weights off-chain via encrypted blob with on-chain key release.
- Randomness: use VRF or drand for fair seeds; commit-reveal as fallback.

## Economic Flows
- Inflows: entry fees, marketplace fees, operator registration, premium access (API credits), sponsorships.
- Outflows: prize payouts, contributor rewards (curators/trainers), operator incentives, bug bounties, liquidity/treasury operations.
- Fee Sinks: protocol fees burned or redirected to treasury; dynamic fee bands based on load and fraud rates.
- Sustainability: target net-deflationary or neutral model with adjustable fee toggles; avoid reflexive emissions.

## Security and Integrity
- Minimal on-chain logic: prefer battle settlement + staking + escrow; avoid complex game logic on-chain.
- Attestations: hatch nodes sign match transcripts; oracle committee posts aggregated results; dispute window with bonds.
- Anti-cheat: client attestation (e.g., TEE/remote attestation if feasible); replay verification; rate limits; anomaly detection on match telemetry.
- Key management: non-custodial default; optional MPC/custody for enterprises. Encourage hardware wallets for operators.
- Upgrades: timelocked governance with guardian veto for critical bugs; staged rollouts with dark launches and allowlists.
- Compliance posture: geo-fencing where required; KYC options for fiat on-ramps; transparent risk disclosures; avoid promising returns.

## Governance Models
- Progressive path:
  1) Foundation stewardship with published roadmaps and KPIs.
  2) Council of operators/curators with veto/ratify rights.
  3) Token- or reputation-weighted votes on parameters (fees, slashing, oracle sets).
  4) Fully on-chain proposals with executable code after audits and timelocks.
- Safeguards: quorum + supermajority for treasury moves; circuit breaker/guardian for halting in emergencies; gradual decay of guardian powers.

## Treasury and Funding
- Sources: initial allocation, marketplace/tournament fees, grants, sponsorships.
- Uses: audits, bounties, infrastructure subsidies for operators, contributor rewards, ecosystem grants.
- Policy: publish quarterly transparency reports; cap emissions; vesting with cliffs for team/early supporters; align unlocks with milestones.

## Deployment Targets
- Priority networks: Ethereum L2s (OP Stack, Arbitrum, Base) for low fees and strong security; alt: Polygon PoS/zkEVM. Avoid new L1 risk.
- Standards: ERC-20 (utility/governance), ERC-721/1155 (agents/artifacts/licenses), EIP-712 signed results, EIP-4337 for better UX (gas abstraction, session keys).
- Bridging: minimize; if needed, use canonical bridges on target L2; avoid custom bridges.

## Phased Rollout
- Phase 0 (Off-chain integrity): hash battle transcripts; publish to IPFS/Arweave; optional notarization on-chain.
- Phase 1 (Managed tournaments): on-chain escrow of entry fees and prize pools; oracle-settled results; single-token utility; operator staking light.
- Phase 2 (Operator staking and slashing): register hatch nodes; require stake; enable slashing for misbehavior/disconnect abuse; reputation accrual begins.
- Phase 3 (Marketplace and forging): on-chain listings and escrow; recipe-based forging; NFT/SBT issuance with off-chain weight delivery.
- Phase 4 (Governance maturation): parameter voting, treasury spend approvals, guardian->timelock transitions; introduce reputation-weighted voting.

## Data and Asset Model
- Agent Identity: on-chain token/NFT representing an agent or license; links to off-chain weights encrypted and stored via decentralized storage; provenance hashes anchor lineage.
- Match Transcript: off-chain log; hash anchored on-chain; signatures from both players and hatch; oracle attestation for payout.
- Reputation: non-transferable score updated by oracle after verified matches; decay over time to encourage recent activity.
- Artifacts/Upgrades: optional NFTs with embedded metadata; execution happens off-chain; hashes anchor authenticity.

## Oracle and Attestation Design
- Committee of independent operators signs results; threshold signature posted on-chain.
- Slashing for oracle equivocation; rotation via governance; transparent performance dashboards.
- Disputes: short challenge window; challengers post bond; automatic replay if deterministic; arbitration council fallback.

## Risk and Mitigation
- Market risk: denominate fees in stablecoins; cap emissions; adaptive fee levers.
- Governance capture: reputation-weighted checks; slow-transfer governance token; quorum rules; guardian brake.
- Technical exploits: audits, formal verification for settlement contracts, bug bounties, canary deployments.
- UX risk: gas abstraction (4337), batched flows, fiat on-ramps; clear status/error surfacing.
- Regulatory risk: avoid investment language; segregate governance vs utility; provide KYC paths where mandated.

## Metrics and Observability
- Integrity: disputed matches rate, oracle equivocation rate, slashing incidents.
- Fairness: disconnect abuse rate, rating inflation metrics, MMR stability.
- Economy: fee/reward ratio, treasury runway, liquidity depth, velocity of utility token, concentration metrics.
- Adoption: DAU of link clients, active operators, tournament participation, marketplace GMV.

## Integration with CocoonHatch/Link
- Hatch nodes sign match results; link clients co-sign; transcripts hashed and optionally anchored.
- Entry fee escrow contract receives buy-ins; oracle posts result; payouts flow automatically.
- Operator registry with staking and reputation; link clients prefer reputable nodes; matchmaking weights toward higher-reputation operators.
- Battle parameters (rounds, timeouts) published on-chain for verifiability; off-chain enforcement in hatch/link.

## Roadmap Checklist
- Smart contracts: escrow + payout; operator registry + staking; oracle aggregator; reputation SBT; NFT schema for agents/licenses.
- Off-chain: transcript signing, hash anchoring, oracle committee tooling, replay verifier.
- Infrastructure: key management guide, monitoring, incident response runbooks, audit pipeline.
- Legal/compliance: terms, disclosures, KYC/AML options, geo controls.
- UX: wallet-lite flows, session keys, gas sponsorship, clear dispute surfaces.

## Conclusion
This blueprint emphasizes utility, security, and progressive decentralization. It scopes crypto to where verifiable settlement and incentives add value while keeping core agent interactions fast and off-chain. Next steps: finalize contract specs, run testnet tournaments with escrowed prizes, instrument integrity metrics, and iterate with operator and player feedback.
