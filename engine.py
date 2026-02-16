"""
推論エンジンモジュール
ベイズ推定と情報エントロピーによる質問選択を実装
"""
import math
from typing import Dict, List, Tuple, Optional

# 尤度計算の定数
# 回答と期待値の差が最大(2.0)の場合でも最小尤度(0.1)を保証
# 計算式: likelihood = 1.0 - diff * LIKELIHOOD_SCALING_FACTOR
# 例: diff=0.0 → 1.0 - 0.0*0.45 = 1.0、diff=2.0 → 1.0 - 2.0*0.45 = 0.1
LIKELIHOOD_SCALING_FACTOR = 0.45

# わからない（不明）回答の判定閾値
UNKNOWN_ANSWER_THRESHOLD = 0.01


class InferenceEngine:
    """ベイズ推定による推論エンジン"""
    
    def __init__(self, entities: Dict[str, Dict[str, float]], questions: Dict[str, str]):
        """
        推論エンジンを初期化
        
        Args:
            entities: エンティティと属性値のマッピング
            questions: 質問IDと質問文のマッピング
        """
        self.entities = entities
        self.questions = questions
        # 各エンティティの事後確率を初期化（一様分布）
        self.probabilities: Dict[str, float] = {}
        self._initialize_probabilities()
        # 既に質問した質問IDのセット
        self.asked_questions: set = set()
    
    def _initialize_probabilities(self) -> None:
        """事後確率を一様分布で初期化"""
        if not self.entities:
            return
        initial_prob = 1.0 / len(self.entities)
        for entity_name in self.entities:
            self.probabilities[entity_name] = initial_prob
    
    def reset(self) -> None:
        """推論状態をリセット"""
        self._initialize_probabilities()
        self.asked_questions.clear()
    
    def _calculate_likelihood(self, expected_value: float, answer: float) -> float:
        """
        回答と期待値から尤度を計算
        
        Args:
            expected_value: エンティティの期待値（-1.0〜1.0）
            answer: ユーザーの回答値（-1.0〜1.0）
            
        Returns:
            尤度（0.1〜1.0）
        """
        diff = abs(expected_value - answer)
        # 差が0なら尤度1.0、差が2.0（最大）なら尤度0.1
        return max(0.1, 1.0 - diff * LIKELIHOOD_SCALING_FACTOR)
    
    def update_probabilities(self, question_id: str, answer: float) -> None:
        """
        回答に基づいてベイズ更新を実行
        
        Args:
            question_id: 質問ID
            answer: 回答値（-1.0=いいえ、-0.5=たぶんいいえ、0.0=わからない、0.5=たぶんはい、1.0=はい）
        """
        self.asked_questions.add(question_id)
        
        # わからないの場合は更新しない
        if abs(answer) < UNKNOWN_ANSWER_THRESHOLD:
            return
        
        # 各エンティティの尤度を計算
        likelihoods: Dict[str, float] = {}
        for entity_name, attributes in self.entities.items():
            if question_id in attributes:
                expected_value = attributes[question_id]
                likelihood = self._calculate_likelihood(expected_value, answer)
                likelihoods[entity_name] = likelihood
            else:
                # 属性が未定義の場合は中立的な尤度
                likelihoods[entity_name] = 0.5
        
        # ベイズ更新: P(entity|answer) ∝ P(answer|entity) * P(entity)
        for entity_name in self.probabilities:
            self.probabilities[entity_name] *= likelihoods[entity_name]
        
        # 正規化
        total = sum(self.probabilities.values())
        if total > 0:
            for entity_name in self.probabilities:
                self.probabilities[entity_name] /= total
    
    def get_best_question(self) -> Optional[str]:
        """
        情報エントロピーに基づいて最適な質問を選択
        
        Returns:
            最適な質問ID、または質問がない場合はNone
        """
        available_questions = [qid for qid in self.questions if qid not in self.asked_questions]
        
        if not available_questions:
            return None
        
        best_question = None
        max_info_gain = -1.0
        
        # 現在のエントロピーを計算
        current_entropy = self._calculate_entropy(self.probabilities)
        
        for question_id in available_questions:
            # この質問をした場合の期待情報利得を計算
            expected_entropy = self._calculate_expected_entropy(question_id)
            info_gain = current_entropy - expected_entropy
            
            if info_gain > max_info_gain:
                max_info_gain = info_gain
                best_question = question_id
        
        return best_question
    
    def _calculate_entropy(self, probs: Dict[str, float]) -> float:
        """
        エントロピーを計算
        
        Args:
            probs: 確率分布
            
        Returns:
            エントロピー値
        """
        entropy = 0.0
        for prob in probs.values():
            if prob > 0:
                entropy -= prob * math.log2(prob)
        return entropy
    
    def _calculate_expected_entropy(self, question_id: str) -> float:
        """
        質問をした場合の期待エントロピーを計算
        
        Args:
            question_id: 質問ID
            
        Returns:
            期待エントロピー
            
        Note:
            計算を簡略化するため、「はい(1.0)」と「いいえ(-1.0)」の2つの極端な
            回答のみをシミュレートします。実際には「たぶんはい(0.5)」などの
            中間的な回答も可能ですが、情報利得の傾向を把握するには十分です。
        """
        # 「はい」と「いいえ」の両方の場合をシミュレート
        expected_entropy = 0.0
        
        for answer in [1.0, -1.0]:
            # この回答になる確率を計算（正規化前のスコア合計）
            total_score = 0.0
            temp_scores = {}
            
            for entity_name in self.entities:
                if question_id in self.entities[entity_name]:
                    expected_value = self.entities[entity_name][question_id]
                    likelihood = self._calculate_likelihood(expected_value, answer)
                else:
                    likelihood = 0.5
                
                score = self.probabilities[entity_name] * likelihood
                temp_scores[entity_name] = score
                total_score += score
            
            # 正規化して確率分布を作成
            temp_probs = {}
            if total_score > 0:
                for entity_name in temp_scores:
                    temp_probs[entity_name] = temp_scores[entity_name] / total_score
            else:
                # すべて0の場合は一様分布
                uniform_prob = 1.0 / len(self.entities) if self.entities else 0.0
                for entity_name in self.entities:
                    temp_probs[entity_name] = uniform_prob
            
            # この回答になる確率（正規化前の合計 / 現在の確率の合計）
            current_total = sum(self.probabilities.values())
            answer_prob = total_score / current_total if current_total > 0 else 0.5
            
            # このシナリオのエントロピーを加算
            expected_entropy += answer_prob * self._calculate_entropy(temp_probs)
        
        return expected_entropy
    
    def get_top_candidates(self, n: int = 3) -> List[Tuple[str, float]]:
        """
        確率が高い上位N件の候補を取得
        
        Args:
            n: 取得する候補数
            
        Returns:
            (エンティティ名, 確率)のリスト
        """
        sorted_entities = sorted(
            self.probabilities.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_entities[:n]
    
    def get_best_guess(self) -> Optional[Tuple[str, float]]:
        """
        最も確率が高いエンティティを取得
        
        Returns:
            (エンティティ名, 確率)、またはNone
        """
        if not self.probabilities:
            return None
        
        best_entity = max(self.probabilities.items(), key=lambda x: x[1])
        return best_entity
    
    def reinforce_entity(self, entity_name: str, question_id: str, answer: float, learning_rate: float = 0.1) -> None:
        """
        正解時に属性値を強化学習
        
        Args:
            entity_name: エンティティ名
            question_id: 質問ID
            answer: 回答値
            learning_rate: 学習率
        """
        if entity_name not in self.entities:
            return
        
        if question_id not in self.entities[entity_name]:
            self.entities[entity_name][question_id] = answer
        else:
            # 既存の値を回答に近づける
            current_value = self.entities[entity_name][question_id]
            new_value = current_value + learning_rate * (answer - current_value)
            # -1.0から1.0の範囲に制限
            self.entities[entity_name][question_id] = max(-1.0, min(1.0, new_value))
