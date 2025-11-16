# セキュリティセットアップガイド

## ⚠️ 重要: API キーの安全な管理

このアプリケーションは外部APIキーを使用します。**絶対にAPIキーをGitにコミットしないでください。**

## ローカル開発環境のセットアップ

### オプション1: .env ファイル使用(推奨 - ローカル開発)

1. `.env.example`を`.env`にコピー:
   ```bash
   cp .env.example .env
   ```

2. `.env`ファイルを編集し、実際のAPIキーを入力:
   ```bash
   KEEPA_API_KEY=your_actual_keepa_key
   RAINFOREST_API_KEY=your_actual_rainforest_key
   CLAUDE_API_KEY=your_actual_claude_key
   ```

3. `.env`が`.gitignore`に含まれていることを確認(既に含まれています)

### オプション2: Streamlit Secrets使用(推奨 - デプロイ)

1. `.streamlit/secrets.toml.example`を`.streamlit/secrets.toml`にコピー:
   ```bash
   mkdir -p .streamlit
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. `.streamlit/secrets.toml`を編集し、実際のAPIキーを入力

3. `.streamlit/secrets.toml`が`.gitignore`に含まれていることを確認

## Streamlit Cloudへのデプロイ

1. Streamlit Cloudダッシュボードにログイン
2. アプリの Settings > Secrets を開く
3. 以下の内容を追加:
   ```toml
   [api_keys]
   KEEPA_API_KEY = "your_actual_keepa_key"
   RAINFOREST_API_KEY = "your_actual_rainforest_key"
   CLAUDE_API_KEY = "your_actual_claude_key"
   ```
4. Save をクリック

## アプリケーション起動

アプリは以下の優先順位でAPIキーを読み込みます:

1. **Streamlit Secrets** (st.secrets)
2. **環境変数** (.env ファイル)
3. **ユーザー入力** (サイドバー)

```bash
streamlit run app.py
```

## セキュリティチェックリスト

- [ ] `.env`ファイルが`.gitignore`に含まれている
- [ ] `.streamlit/secrets.toml`が`.gitignore`に含まれている
- [ ] `.env.example`にはプレースホルダーのみ(実際のキーなし)
- [ ] 実際のAPIキーがGitにコミットされていない
- [ ] Streamlit Cloudの秘密鍵が設定されている(デプロイ時)

## トラブルシューティング

### "API key not found" エラー

1. `.env`ファイルが存在し、正しいキーが入力されているか確認
2. Streamlit アプリを再起動
3. サイドバーで手動でAPIキーを入力(一時的)

### Streamlit Cloudでエラー

1. Settings > Secrets が正しく設定されているか確認
2. TOML形式が正しいか確認(引用符、等号記号)
3. アプリを再デプロイ

## API キーの取得

- **Keepa API**: https://keepa.com/#!api (無料プラン: 1トークン/分、有料プラン推奨)
- **RainforestAPI**: https://www.rainforestapi.com/ (無料プラン利用可)
- **Claude API**: https://console.anthropic.com/ (従量課金)

## セキュリティのベストプラクティス

1. **定期的なキーローテーション**: 3-6ヶ月ごとにAPIキーを再発行
2. **権限の最小化**: APIキーには必要最小限の権限のみ付与
3. **監視**: API使用量を定期的にチェックし、異常な使用を検出
4. **バックアップ**: APIキーを安全な場所(パスワードマネージャー等)にバックアップ
5. **共有禁止**: APIキーを他人と共有しない、公開リポジトリにコミットしない
