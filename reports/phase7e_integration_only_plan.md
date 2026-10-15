# Phase7E：獨立積分準備計畫（未授權執行）

`INDEPENDENT_INTEGRATION_STATUS: NOT_AUTHORIZED`。已實際執行的是 card/include **準備與驗證**及拒絕案例；不是 survey、refine、新矩陣元素或新 integral。沒有更動 MG 安裝、B/C process、grid 或事件。

入口為 [prepare_integration_only.sh](../simulation/hh_signal/integration_audit/prepare_integration_only.sh)。在既有 WSL 工具環境、repository 根目錄執行：

```bash
bash simulation/hh_signal/integration_audit/prepare_integration_only.sh \
  --output "$HOME/simulations/hh_integration_audit/my_plan_01" \
  --seeds 910001 910019 910037 910061 \
  --points 250 --iterations 5 --accuracy 0.005 --max-hours 4
bash simulation/hh_signal/integration_audit/prepare_integration_only.sh \
  --output "$HOME/simulations/hh_integration_audit/my_plan_01" --validate
```

每個 output 必須為新目錄；不重裝、不覆蓋。複製精確 B param card；run card 僅設 nevents=0 與新 seed。每次重新建立原生 RunCardLO writer，重做三次 include preview 並確認全域／兩 beam 均 cteq6l1。plan/manifest 固定 hashes、上限、禁止命令與未授權狀態。實際準備版本見 [prepared_plan](../simulation/hh_signal/integration_audit/evidence/prepared_plan/plan.json)，原生 CLI 四個實測案例見 [preparation_cli_checks](../simulation/hh_signal/integration_audit/evidence/preparation_cli_checks.json)。

```bash
# 必須 exit 2；拒絕發生在讀寫 output 或呼叫 MG5 之前。
bash simulation/hh_signal/integration_audit/prepare_integration_only.sh \
  --output "$HOME/simulations/hh_integration_audit/my_plan_01" --execute
```

後續 native survey command 的具體設計已寫入 plan，例如 `survey phase7e_seed_910001 --points=250 --iterations=5 --accuracy=0.005`。它不是本階段可執行的 integral backend。**nevents=0 不能證明零 LHE**：native survey 本身可產生內部 weighted candidate scratch。執行前必須另外審核 writer suppression／零保留 guard，監測所有寫入、拒絕 store/combine/refine/generate_events/shower/detector，並在結束檢查零 retained event records。這項 runtime 驗證目前 BLOCKED；不以準備成功替代執行成功。

四個量測 replica 的物理 integrand 須一致：CTEQ6L1、αs(MZ)=.13、一圈 running、原有限質量 loop source、13 TeV、μR=μF=mHH/2、inclusive HH。每個從新 process/workspace 與新 grid adaptation 起始，禁止匯入 B/C grids。先比對實際 include、初始化 PDF/grid、running 與 seed，再接受積分結果。新 seeds 不重用 21、20261121、20261122。

收斂評估設計：

1. 保留 warmup/adaptation 與 measurement 的明確界線、逐 iteration mean/error/χ、積分點數、實際 ME calls、grid hashes、tail/loop 穩定性及終止原因。不能將同 grid 的 survey/refine 當獨立 replica。
2. 至少四個獨立 replica；以 replica 間樣本標準差/√R 與 t(R−1) 區間報告均值，另列各 run 內部誤差。R=4 的自由度很低；區間寬就判定 INCONCLUSIVE，不把內部 0.5% goal 當 empirical coverage。
3. 事先指定固定 budget checkpoints／保留 measure batch；比較增加 budget 前後均值、尾部與 grid 穩定性。共同樣本 checkpoints 相關，須 paired 差或另開獨立 budget arm；不可當獨立點套 χ²。目標每 run 內部相對誤差 0.5%、budget 間差 1% 是驗收目標，不保證已達。
4. 正式 fixed-grid measurement 與任何第二組 budget arm 尚須確認原生控制／zero-retention guard，並在獨立授權中明列。多次看結果後停止不能沿用未修正的固定樣本 CI；以預先固定 batches 與 replica endpoint 為準。達不到精度則停止、報告有界結果，不自動擴產。

初始提案 aggregate wall budget ≤4h、單 job/單 worker、額外 disk≤5 GiB。成本模型以 B 平均 .0625797962 秒/ME 評估、四個 exact helicity、迭代點數保守倍增估算 124000 calls、約 2.16h，再乘 1.5 margin 約 3.23h；不是效能保證。250 points×5 iterations 是可審核的初始上限，並不能保證完整 convergence study。1000 points 的同設定預估超過上限，實際命令已拒絕且未建立 output。任何擴 budget、固定 grid arm、NNPDF matched arm／PDF×running 分解均須另行授權。

執行前需核准的是具體積分-only 實作、零保留 guard、工作預算與 endpoints；這次沒有請求或推定授權。
