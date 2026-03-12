# 🛡️ Jun's Airgap Guard

![Version](https://img.shields.io/github/v/release/wakaya/ComfyUI-JunsAirgapGuard)
![License](https://img.shields.io/github/license/wakaya/ComfyUI-JunsAirgapGuard)
![ComfyUI Custom Node](https://img.shields.io/badge/ComfyUI-Custom%20Node-8A2BE2)

A lightweight custom node for ComfyUI that checks whether a specified URL is reachable and optionally blocks workflow execution.

ComfyUI 用の軽量カスタムノードです。指定した URL への到達性を確認し、条件に応じてワークフロー実行を停止できます。

---

## Overview / 概要

**Jun's Airgap Guard** is designed for workflows that should not proceed when outbound connectivity is available, or conversely, should not proceed unless a target is reachable.

**Jun's Airgap Guard** は、外向き通信が可能な状態では進めたくないワークフロー、あるいは逆に特定の接続先へ到達できる時に続行させたい方向けの「チェックと防御のためのノード」です。

Typical use cases:

- Verify that a public URL is **not reachable** before running an offline generation workflow
- Verify that a local or internal URL **is reachable** before continuing
- Display the current status directly on the node with a colored badge

主な用途:

- オフライン生成前に、公開 URL へ **到達できない** ことを確認する
- ローカル URL や内部 URL へ **到達できる** ことを確認する
- ノード上に色付きバッジで現在状態を表示する

---

## Features / 特徴

- URL reachability check by `HEAD` request
- Colored status badge on the node
- Block execution when reachable
- Block execution when unreachable
- Report-only mode
- Simple i18n support for English and Japanese
- V1-friendly recheck trigger using an integer probe token

- `HEAD` リクエストによる到達性確認
- ノード上の色付きステータス表示
- 到達可なら停止
- 到達不可なら停止
- 表示のみモード
- 日本語・英語の簡易 i18n 対応
- V1 向けの再確認用整数トークン対応

---

## Installation / インストール

### Option 1: Manual install / 手動インストール

Clone this repository into your `ComfyUI/custom_nodes` directory.

このリポジトリを `ComfyUI/custom_nodes` に配置してください。

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/YOUR_NAME/JunsAirgapGuard.git

Then restart ComfyUI and reload the browser.

その後、ComfyUI を再起動し、ブラウザも再読み込みしてください。

Node Information / ノード情報

Node name / ノード名: 🛡️ Jun's Airgap Guard

Category / カテゴリ: Jun's Nodes

Inputs / 入力
url

Target URL to test. Only http:// and https:// are supported.

確認対象 URL。http:// と https:// のみ対応。

timeout_seconds

Timeout for the connectivity check.

接続確認のタイムアウト秒数。

mode

Available modes:

block_if_reachable

block_if_unreachable

report_only

動作モード:

block_if_reachable = 到達可なら停止

block_if_unreachable = 到達不可なら停止

report_only = 表示のみ

probe_token

An integer token used to force re-checking in V1 workflows.

V1 ワークフローで再確認を強制するための整数トークンです。

Status Badge / ステータス表示

The node displays a colored badge directly on itself:

Gray: idle

Yellow: checking

Green: reachable

Red: unreachable

Purple: invalid URL

ノード上に色付きバッジで状態を表示します:

灰色: 未確認

黄色: 確認中

緑色: 到達可

赤色: 到達不可

紫色: URL不正

Notes / 注意事項

This node checks reachability to the specified URL, not absolute “internet on/off” state.

このノードが判定するのは、絶対的な「オンライン / オフライン」ではなく、指定 URL への到達性です。

For example:

A public website may be unreachable while local network access still works

A local address may be reachable even if internet access is blocked

たとえば:

公開サイトに届かなくても LAN 内通信は通っている場合があります

インターネット遮断中でもローカルアドレスには到達できる場合があります

Recommended Usage / 推奨運用

For ComfyUI V1 workflows, connect a randomized integer primitive to probe_token so the node re-checks every run.

ComfyUI V1 では、probe_token に毎回変化する整数を接続すると、毎回再確認しやすくなります。

This node pairs well with tools such as Airgap Tray.

このノードは Airgap Tray のような外向き通信制御ツールと相性が良いです。

File Structure / ファイル構成
JunsAirgapGuard/
├─ __init__.py
├─ juns_airgap_guard.py
├─ locales/
│  ├─ en/
│  │  ├─ nodeDefs.json
│  │  └─ main.json
│  └─ ja/
│     ├─ nodeDefs.json
│     └─ main.json
└─ web/
   └─ js/
      └─ juns_airgap_guard.js
License / ライセンス

MIT License

Credits / クレジット

Created by Jun Wakaya.
Built for ComfyUI custom workflows with bilingual UI support.

日英 UI 対応の ComfyUI カスタムワークフロー向けに作成。
