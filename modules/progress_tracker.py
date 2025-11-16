"""
進捗トラッカー
API呼び出しやデータ処理の進捗を視覚化
"""
import streamlit as st
from typing import Optional

class ProgressTracker:
    """リアルタイムプログレスバー"""

    def __init__(self):
        self.progress_bar: Optional[st.delta_generator.DeltaGenerator] = None
        self.status_text: Optional[st.delta_generator.DeltaGenerator] = None
        self.current_step: int = 0
        self.total_steps: int = 0

    def start(self, total_steps: int, container=None):
        """
        進捗追跡を開始

        Args:
            total_steps: 総ステップ数
            container: Streamlitコンテナ（オプション）
        """
        self.total_steps = total_steps
        self.current_step = 0

        if container:
            self.progress_bar = container.progress(0)
            self.status_text = container.empty()
        else:
            self.progress_bar = st.progress(0)
            self.status_text = st.empty()

    def update(self, message: str, increment: int = 1):
        """
        進捗を更新

        Args:
            message: 表示するメッセージ
            increment: 増加ステップ数（デフォルト: 1）
        """
        self.current_step += increment
        progress = min(self.current_step / self.total_steps, 1.0)

        if self.progress_bar:
            self.progress_bar.progress(progress)

        if self.status_text:
            percentage = int(progress * 100)
            self.status_text.text(f"⏳ {message} ({self.current_step}/{self.total_steps}) - {percentage}%")

    def complete(self, message: str = "✅ 完了！"):
        """
        進捗を完了状態に

        Args:
            message: 完了メッセージ
        """
        if self.progress_bar:
            self.progress_bar.progress(1.0)

        if self.status_text:
            self.status_text.text(message)

    def error(self, message: str):
        """
        エラー状態を表示

        Args:
            message: エラーメッセージ
        """
        if self.status_text:
            self.status_text.error(f"❌ {message}")

    def clear(self):
        """進捗表示をクリア"""
        if self.progress_bar:
            self.progress_bar.empty()
        if self.status_text:
            self.status_text.empty()


def create_progress_container():
    """
    進捗表示用のコンテナを作成

    Returns:
        Streamlitコンテナ
    """
    return st.container()
