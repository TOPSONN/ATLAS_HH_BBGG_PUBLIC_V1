# Phase7F：有效設定鎖

基線 PR21=`28862bed06451723ba17c11fbca9f88b6abb8ee7`；所有歷史物理來源、events、weights、cards、integration logs 與報告保持原 bytes。新 source implementation 僅在 legacy campaign、source generation 與 child launcher 加入拒絕 hooks；另兩處相容編輯為 payload allowlist 與 legacy CI pin。

目標：MG5 3.5.16 loop_sm，`g g > h h [noborn=QCD]`，MH/MT/MB=125/173/4.7 GeV、κλ=κt=1、CTEQ6L1、αs(MZ)=.130、一圈 running，13 TeV、μR=μF=mHH/2。[configuration_lock.json](../simulation/hh_signal/config_lock/configuration_lock.json) 綁定 682 個 source/library inputs、149 個 build auxiliaries、process/MadLoop cards、模板與精確 native writer/driver identities。

新 param template 只將舊 B card 的 SMINPUTS[3]=.129783 改為 .130；新 run template 明確補上 ickkw=0。這些是新增 Phase7F 模板，沒有修改任何舊卡片。每次從精確文字建立全新 RunCardLO，不帶鄰近檔案位置；三次獨立 include 寫出必須相同，所有 PDF 欄位必須為 cteq6l1。

實際 drift probe 在新的隔離診斷目錄重現 reused working-card writer 的全域 cteq6l1→nn23lo1，beam sublabels 仍 cteq6l1；fresh writer 三次均維持 cteq6l1。這驗證防護機制，不把完整歷史 Python 狀態宣稱已重建。

原生 probes 實際初始化 CTEQ6L1 table、pdfwrap、ALPHAS、get_pdfup/get_base/offset；不是從 LHE header 猜測。五個尺度 91.188/125/250/500/1000 GeV 的 αs 與獨立一圈公式比較，容許相對差 1e−10。四個完整隔離 driver 另在第一個 helicity/ME 呼叫之前執行 native gate，核對實際 common blocks 的 global/beam PDF、αs、running、HEPRUP PDFSUP=10042、masses、beam/scales 與 seed，然後退出。

Requested seed=launch request=prepared Banner=compiled include=native base=recorded run identity。working seed 被重設 0、continuation 退回 21、missing evidence 均拒絕。RANMAR 內部乘 31300 與 iproc/moffset 不是原始來源 seed。四個未來 measurement streams 的 moffset=1 尚未執行；不得將準備的 Banner 稱作新物理 LHE 的實際 embedded source card。

831 個原生 inputs、support cards、templates、關鍵 pinned MG5 sources 均在準備前後核對；隔離 build 的實際 Source/run_card.inc 也重新解析驗證，編譯產物與完整 workspace inventory 另有 SHA256。完整原生 driver 已編譯、初始化出口與拒絕路徑已執行，但 **沒有積分、沒有新 ME evaluation、沒有物理事件**。

此防護關閉 repository 的受控 HH 實際產生入口；不能聲稱約束使用者手動執行任意外部 MG5。歷史物理設定與有效值依 Phase7E 更正保留，並不因本次新設定鎖而自動修正。
