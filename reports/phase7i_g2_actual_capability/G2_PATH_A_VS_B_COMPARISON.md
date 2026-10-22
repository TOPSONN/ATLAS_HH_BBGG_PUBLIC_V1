# Path A versus B

| 比較 | A：原契約 | B-V2：待接受的WSL研究架構 |
|---|---|---|
| 可行性 | 此host未證成joint全部成本與強停止 | Linux documented hierarchy可作候選；manager/delegation權限未驗證 |
| 重現性 | 需同時固定Windows/VM/kernel與全成本capture | 固定job/source/device/observer，external成本另報；仍需真實readback |
| 安全 | 原始保護與零超額要求不放寬 | root/history/device保護保留，CPU/RAM暫態及external邊界較弱 |
| 複雜度 | 缺joint host/guest enforcer，工作量未可量測 | 可重用controller/slots/ledger；新protected acquisition與observer未部署 |
| 科學用途 | 未成立前不能啟動物理 | 可接受overshoot失敗判定及external成本時較實際，但不是ATLAS認證 |
| 依賴 | 實際受控平台＋全部原A強保證 | 條款、manager、fixed device、exclusivity、protected observer、kernel正反、bounded logs |
| 剩餘風險 | 沒有證成上界 | scheduler/outer失效、OOM、外部成本及durability未知，均需明示 |

B的8組阻擋由具名清單計數（另含guest異步kernel成本歸屬），不是概率或信心分數。沒有新硬體可用證據。普通大physical disk不能只切4MiB filesystem來冒充已審S4 4MiB whole-device identity；fixed virtual LUN亦須不grow、不thin/sparse、不在protected backing，並另證allocated成本與host-writer排除，現在沒有合格candidate。

推薦先審B-V2三份exact文件，而不是繼續把source-only工作當作A的實機驗收。若不能接受較弱邊界，停止此WSL部署路徑，先找能提供原A實際證據的平台；不自動遷移或安裝。
