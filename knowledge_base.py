"""
知識ベースの管理モジュール
JSONファイルからの読み込み・保存機能を提供
"""
import json
import os
from typing import Dict, List, Any


class KnowledgeBase:
    """知識ベースを管理するクラス"""
    
    def __init__(self, filepath: str = "knowledge_base.json"):
        """
        知識ベースを初期化
        
        Args:
            filepath: JSONファイルのパス
        """
        self.filepath = filepath
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.questions: Dict[str, str] = {}
        self.load()
    
    def load(self) -> None:
        """JSONファイルから知識ベースを読み込む"""
        if not os.path.exists(self.filepath):
            self._initialize_default_data()
            self.save()
            return
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.entities = data.get('entities', {})
                self.questions = data.get('questions', {})
        except (json.JSONDecodeError, IOError) as e:
            print(f"警告: データの読み込みに失敗しました: {e}")
            self._initialize_default_data()
    
    def save(self) -> None:
        """知識ベースをJSONファイルに保存"""
        data = {
            'entities': self.entities,
            'questions': self.questions
        }
        
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"エラー: データの保存に失敗しました: {e}")
    
    def add_entity(self, entity_name: str, attributes: Dict[str, float]) -> None:
        """
        新しいエンティティを追加
        
        Args:
            entity_name: エンティティ名
            attributes: 質問IDと属性値(-1.0〜1.0)のマッピング
        """
        self.entities[entity_name] = attributes
    
    def update_attribute(self, entity_name: str, question_id: str, value: float) -> None:
        """
        エンティティの属性を更新
        
        Args:
            entity_name: エンティティ名
            question_id: 質問ID
            value: 新しい属性値(-1.0〜1.0)
        """
        if entity_name in self.entities:
            self.entities[entity_name][question_id] = value
    
    def add_question(self, question_id: str, question_text: str) -> None:
        """
        新しい質問を追加
        
        Args:
            question_id: 質問ID
            question_text: 質問文
        """
        self.questions[question_id] = question_text
    
    def get_all_entities(self) -> Dict[str, Dict[str, float]]:
        """全エンティティを取得"""
        return self.entities
    
    def get_all_questions(self) -> Dict[str, str]:
        """全質問を取得"""
        return self.questions
    
    def _initialize_default_data(self) -> None:
        """デフォルトの初期データで初期化"""
        # 質問IDと質問文
        self.questions = {
            'q1': 'それは哺乳類ですか？',
            'q2': 'それは飛べますか？',
            'q3': 'それはペットとして飼えますか？',
            'q4': 'それは水中で生活しますか？',
            'q5': 'それは肉食ですか？',
            'q6': 'それは大きい動物ですか？（人間より大きい）',
            'q7': 'それは鳴き声を出しますか？',
            'q8': 'それは足が4本ありますか？'
        }
        
        # エンティティと属性値（-1.0=いいえ, 0.0=わからない, 1.0=はい）
        self.entities = {
            '犬': {
                'q1': 1.0,   # 哺乳類: はい
                'q2': -1.0,  # 飛べる: いいえ
                'q3': 1.0,   # ペット: はい
                'q4': -1.0,  # 水中: いいえ
                'q5': 0.5,   # 肉食: たぶんはい
                'q6': -0.5,  # 大きい: たぶんいいえ
                'q7': 1.0,   # 鳴き声: はい
                'q8': 1.0    # 足4本: はい
            },
            '猫': {
                'q1': 1.0,   # 哺乳類: はい
                'q2': -1.0,  # 飛べる: いいえ
                'q3': 1.0,   # ペット: はい
                'q4': -1.0,  # 水中: いいえ
                'q5': 1.0,   # 肉食: はい
                'q6': -1.0,  # 大きい: いいえ
                'q7': 1.0,   # 鳴き声: はい
                'q8': 1.0    # 足4本: はい
            },
            '象': {
                'q1': 1.0,   # 哺乳類: はい
                'q2': -1.0,  # 飛べる: いいえ
                'q3': -1.0,  # ペット: いいえ
                'q4': -1.0,  # 水中: いいえ
                'q5': -1.0,  # 肉食: いいえ
                'q6': 1.0,   # 大きい: はい
                'q7': 1.0,   # 鳴き声: はい
                'q8': 1.0    # 足4本: はい
            },
            'ペンギン': {
                'q1': -1.0,  # 哺乳類: いいえ
                'q2': -1.0,  # 飛べる: いいえ
                'q3': -0.5,  # ペット: たぶんいいえ
                'q4': 0.5,   # 水中: たぶんはい
                'q5': 0.5,   # 肉食: たぶんはい
                'q6': -1.0,  # 大きい: いいえ
                'q7': 1.0,   # 鳴き声: はい
                'q8': -1.0   # 足4本: いいえ
            },
            '金魚': {
                'q1': -1.0,  # 哺乳類: いいえ
                'q2': -1.0,  # 飛べる: いいえ
                'q3': 1.0,   # ペット: はい
                'q4': 1.0,   # 水中: はい
                'q5': -1.0,  # 肉食: いいえ
                'q6': -1.0,  # 大きい: いいえ
                'q7': -1.0,  # 鳴き声: いいえ
                'q8': -1.0   # 足4本: いいえ
            }
        }
