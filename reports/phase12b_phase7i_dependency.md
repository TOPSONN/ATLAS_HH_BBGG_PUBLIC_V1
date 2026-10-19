# Phase12B：Phase7I Route-A 的 runtime configuration 依賴影響

結論：對精確 `b80e16775bf141e45f4048c7197a8a99befaed51` 的 **已審查 Route-A contract**，安裝位置 `input/mg5_configuration.txt` 是 **NOT_BOUND_BY_REVIEWED_CONTRACT**。這不等於目前 Phase7I build 或 binary 已重新通過，也不是對所有 compiler／loader／外部隱含讀取的保證；未執行的外部 runtime 行為保留 **UNKNOWN**。不能將 Phase11 的 raw-config drift 自動推論成所有 Phase7I frozen bytes 失效。

## 審核範圍與精確身分

舊 checkout 為 `/home/btu/projects/atlas_hh_phase7i_b80e1677`。本次只讀來源、JSON descriptor、Git blob 與 AST；不匯入舊 runtime module，不呼叫 prepare-review、HumanReview、verify_checkout、check_build、compiler、ldd、native preflight 或 Stage A。新的 auditor 使用固定的唯讀 Git `rev-parse HEAD` 與 `cat-file blob REV:path`，對選定 25 個 critical source/descriptor 檔比較實際 raw bytes 與指定 commit 的 Git blob，並在審核前後檢查相同來源與 distinct local selector。

目標的邏輯路徑：`/home/btu/opt/mg5amcnlo/input/mg5_configuration.txt`。實體路徑由 symlink resolution 記錄，預期位於 `.local/share/atlas-hh-phase6a/mg5-release-v3.5.16/input/`。本子任務不讀取或發布目標 raw configuration bytes；Phase12A 負責三個分開 process 的實際觀察與 drift 記錄。

| 關鍵來源 | 精確 b80 SHA256 |
|---|---|
| `integration_runtime/route_a.py` | `4da8b8a4332740ffb872728b111134d0539c9c5e488c6a74276627d3d2b12e18` |
| `integration_runtime/build.py` | `1cdb81e25d0544b5d7b630d8a34bdb1dd92d36083b00925017d900ab032a0736` |
| `integration_runtime/build_plan.py` | `243a45eb8542aea66cbf855b061e5d7a2fb644d9f93046c6ab27dcebd276936f` |
| `integration_runtime/run.py` | `c45924ca813b58c738364fefa893535586a681da977c820e03cf1a2cc5fa05f1` |
| `simulation/hh_signal/campaign/common.py` | `23c28f05d9211a925eca37759e806fdd99a8b904972d1df2926f6cfef5f37a97` |
| `final_closure/src/plans.py` | `b1a18c8e29d47c85afea2425f1a3c04c007bcf71fac37139b5f0cf8e01ad2709` |
| `config_lock/configuration_lock.json` | `e58ab70af11827b7f7b206cbfbb3e7c7dff24cd5ab78a23a9f626b8c7db128dd` |
| `metadata/phase7i_builder_review_contract.json` | `c22eafdbcabb07550c5ffa9eddb39fd8100993fd3bf70d09ad5b1c60a1d57452` |
| `metadata/phase7_final_route_a_toolchain.json` | `2ae687df6eb9269681d11e60dbb60333a5c896c16ac13e567544599a11ba3c7d` |
| `metadata/phase7a_model_manifest.json` | `18e239fa878a30c809be461e62ca326e4b423a97f71029111f873aea88819fc3` |

表內 `integration_runtime/`、`final_closure/`、`config_lock/` 分別位於 `simulation/hh_signal/final_closure/`、`simulation/hh_signal/` 的相應子樹；完整無縮寫路徑、檔案長度、SHA256、逐行 witness 及 AST function 範圍保存在 `phase7i_dependency_impact.json`。以上雜湊是來源身分，不是新生成的 build receipt。

## 明列 inventory 的完整 membership 檢查

| contract／inventory | 項數 | 路徑的基底 | 對目標判定 |
|---|---:|---|---|
| `configuration_lock.json:frozen_runtime_sources` | 682 | 原 B100 `7b/source/process` | NOT_BOUND_BY_REVIEWED_CONTRACT |
| `configuration_lock.json:runtime_build_auxiliary` | 149 | 原 B100 `7b/source/process` | NOT_BOUND_BY_REVIEWED_CONTRACT |
| `phase7i_builder_review_contract.json:frozen_process_dependencies` | 71 | 原 B100 `7b/source/process` | NOT_BOUND_BY_REVIEWED_CONTRACT |
| 同上 `frozen_card_identities` | 24 | repository | NOT_BOUND_BY_REVIEWED_CONTRACT |
| `phase7a_model_manifest.json:installed_model_files` | 28 | installed MG5 root | NOT_BOUND_BY_REVIEWED_CONTRACT |
| `phase7_final_route_a_toolchain.json` 解碼後 complete inventory | 8166 | 明確 toolchain root | NOT_BOUND_BY_REVIEWED_CONTRACT |
| `route_a.full_sources()` 規則的獨立靜態重建 | 276 | repository | NOT_BOUND_BY_REVIEWED_CONTRACT |

每份清單都檢查非空、canonical relative path、沒有 `..`／absolute path／重複項，且 SHA256 格式完整。toolchain 的 8166 筆 lossless parent-directory groups 重新解碼，核對 descriptor 裡的 `file_count` 與 canonical complete-file-list digest。membership 也解析可能的 path alias，避免把另一個名字的 symlink 指向目標誤稱為不相依。

這裡的 682＋149＝831 是**現有 descriptor 的 frozen process 檔案數**。本次沒有重雜湊全部 831 native payload 或 8166 toolchain payload，也沒有重新測量現有 binary 的 linkage；因此不宣稱那些 payload 目前完整通過。檢查的是精確來源 contract 究竟列入哪些路徑、如何使用它們，以及本次選定 descriptor 本身是否仍等於 b80 Git blob。

## 正向追蹤實際呼叫與資料流

判定不是只搜尋字串後宣稱不存在，而是逐段核對已審查的建置／讀取邊界。

1. `build.prepare()`（build.py:21–38）先取得 BUILD_ONLY review 與 exact source/Git binding，才讀 **另一個檔案** `.local/mg5_installation.json`。它取 `mg5_path`、`toolchain_prefix`、`source_commit`；這個 selector 不是安裝樹 `input/mg5_configuration.txt`。
2. `campaign.common.mg_environment()`（54–57）由 selector 的 toolchain prefix 組成 PATH／LD_LIBRARY_PATH；並未呼叫 MG5 Python interface 讀取 global configuration。
3. `build.prepare()`（33–38、60–86）從已存在 B100 process 複製 frozen 831 項；驗證 installed model 清單與固定 physics/card identities，套用已審查 overlay，不重新生成 MG5 process。
4. `src.plans.verify_model_sources()`（6–9）逐一雜湊 `installed_model_files` 明列的 28 項。清單的 models/loop_sm、LICENSE、VERSION 不是 installed global configuration。
5. `build_plan.plan()` 明列 compiler、Fortran／C sources、include dirs、`process/lib` 與 link libraries。builder 透過 `bounded_invoke` 執行這些參數；該路徑不使用 MG5 `MasterCmd`、run-card parser 或 `bin/mg5_aMC`。
6. `build.prepare()`（94–106）的預檢是新 executable 的 native input-parse preflight。`validate_preflight()` 檢查保存的 PDF、α_s、mass、scale、beam 與零 ME protocol，不能解讀成已觀察 global MG5 config；本次完全沒有執行這些預檢。
7. `run.check_build()`（31–38）經 source/Git check、`route_a.validate_receipt()`、linkage 與 card/source/immutable inventories 進行驗證。`route_a.full_sources()` 的正向 root/suffix 規則只列 repository 內的來源與明列 metadata/cards，沒有因此把安裝 MG5 整棵樹隱含納入。

`full_sources()` 會雜湊某些歷史 generation adapter 的**程式來源**，但 provenance 綁定一份程式不等於這條 Route-A path 執行了該 adapter。其他舊流程可能曾使用 MG5 全域設定；那不是本次可以由單一全域 config 漂移推得的 active dependency。

## 四種分類的適用範圍

- **DIRECT_DEPENDENCY**：若明列 inventory 的實體目標正是該檔，或選定 callchain 明確直接讀取，不能標成缺席。
- **INDIRECT_DEPENDENCY**：必須有具體可追蹤的間接讀取鏈，不由相似檔名、使用過 MG5 或共享路徑推定。
- **NOT_BOUND_BY_REVIEWED_CONTRACT**：本次目標在上述明列範圍與已審查資料流中的結論。
- **UNKNOWN**：未執行 compiler／loader／native runtime 的外部隱含讀取、歷史未觀測 caller，以及目前 build 是否可通過；不得由本靜態結果消除。

所以 Phase11 raw drift **不自動使已凍結 Phase7I process、model、toolchain 或 executable 的 bytes 改變**。反過來，本次也沒有給 Phase7I 新 PASS、新 baseline approval 或任何 restart capability。舊 `98aa0054…` complete receipt 仍只屬原有歷史證據；BUILD_ONLY 授權已 consumed，不能沿用。

## 本次可執行的靜態命令

```sh
python3 -B analysis/phase12/scripts/audit_phase7i_dependency.py \
  --phase7i-checkout /home/btu/projects/atlas_hh_phase7i_b80e1677 \
  --output /home/btu/simulations/hh_phase12/run_01/phase7i_dependency_impact.json
```

CLI 拒絕覆寫既有 output。22 項方法測試已實跑通過，包括 direct/indirect/unknown 分類、沒有正向 callchain 時不可只靠缺席得到結論、symlink alias、舊 revision、缺 hash、raw whitespace 與 existing output 拒絕。這些是 synthetic method fixtures，沒有引入新 physics evidence。完整 CLI 已由 root 的受控既有來源審核實際執行，結果另見下述收據；單元測試不代替這次 source audit。

**沒有新 prepare-review、HumanReview、Route-A build、native preflight、Stage A、MG5 parser、ME、integral 或事件。**

## 實際 source-audit 收據

`phase7i_dependency_impact.json` 已實際建立：34,196 bytes，SHA256 `d3f7062b0480d771742df576ca693d557ae3481107f2214abe34cd8c2cf30ce2`。結果為 `NOT_BOUND_BY_REVIEWED_CONTRACT`；25 份 critical source/descriptor 與 exact b80 Git blob 相符，12 組來源 witnesses、10 個 AST function call-site 記錄、7 份完整 inventory membership 檢查；repository source binding 這次重建為 276 項。所有 inventory 的目標 matches 都為空，外部 implicit runtime 仍為 UNKNOWN。這是實際執行的**新靜態 auditor**，不是執行 Phase7I 自身的任何 preflight 或 build。
