"""
VOC 인사이트 처리 스크립트 v2
Usage: python process.py --input input.csv --output data.json

CSV 전제: 브랜드별 핵심 아이템 리뷰만 사전 필터링된 파일
출력 구조: 브랜드 → 아이템 → 피드백 카테고리(언급수 순) → 대표 리뷰 3+3
"""
import argparse
import json
import re
from collections import Counter
from difflib import SequenceMatcher

import pandas as pd

from item_mapping import (
    BRAND_CODE, ITEM_MAP, DEFAULT_CATEGORY, SEASON_ORDER,
    SYNONYM_MAP, BRAND_NAME_ALIAS, get_item_category,
)

# ---------------------------------------------------------------------------
# 피드백 카테고리 정의
# ---------------------------------------------------------------------------

FEEDBACK_CATEGORIES = {
    "상품품질": [
        "봉제", "박음질", "울풀림", "내구성", "변형", "뜯어짐",
        "구멍", "보풀", "올", "터짐", "세탁", "수축", "마감", "오염",
    ],
    "사이즈·핏": [
        "사이즈", "기장", "허리", "밴드", "핏", "오버핏", "슬림핏",
        "품", "폭", "길이", "실측",
    ],
    "디자인·컬러": [
        "색상", "디자인", "패턴", "트렌드", "스타일",
    ],
    "가격·가성비": [
        "가격", "가성비", "돈값", "아깝다", "할인", "세일",
    ],
    "구매·배송 경험": [
        "배송", "포장", "교환", "반품", "환불", "고객센터", "재구매",
    ],
}

NEGATIVE_KEYWORDS = [
    # 실망/불만
    "아쉽다", "아쉬워요", "아쉽네요", "아쉬운",
    "별로예요", "별로네요", "별로다", "별로인",
    "실망이에요", "실망스러워", "실망했", "최악이에요", "최악이다", "최악",
    "불편해요", "불편한", "불편하다", "불만이에요", "불만족",
    # 품질 문제
    "터졌어요", "터졌", "뜯어짐", "뜯겼", "불량이에요", "불량품", "불량",
    "하자가", "하자 있", "오염됐", "변형됐",
    "줄어들었", "줄어들어요", "줄었어요", "수축됐",  # "줄어들" 완성형으로 교체
    # 가격/후회
    "아깝다", "아까워요", "돈 아까워", "돈아까워",
    "후회해요", "후회됩니다", "후회했",
    # 반품/교환 의도
    "환불했", "환불 요청", "반품했", "반품 요청",
    "다시는 안", "절대 안 사", "안 살 것",
    # 기타
    "기대 이하", "안 좋아요", "안좋아요", "달라요", "오차가",
]

POSITIVE_KEYWORDS = [
    "좋아요", "좋습니다", "좋다", "너무 좋아",
    "만족해요", "만족스러워", "만족합니다",
    "예쁘다", "예뻐요", "예쁩니다", "이쁘다", "이뻐요",
    "딱이다", "딱이에요", "딱 맞아요",
    "재구매", "또 살", "또 샀", "또 구매",
    "추천해요", "추천합니다", "강추",
    "완벽해요", "완벽합니다",
    "빠르다", "빠르게", "빨리 왔",
    "친절해요", "친절하게",
    "기대 이상", "기대보다 좋", "최고예요", "최고입니다",
    "마음에 들어요", "마음에 들어",
]

# 브랜드명은 동적으로 추가됨 (아래 init_stopwords 참고)
STOPWORDS = {
    "이것", "그것", "저것", "이거", "그거", "저거", "여기", "거기",
    "정말", "너무", "조금", "그냥", "진짜", "완전", "꽤나", "약간",
    "매우", "아주", "엄청", "무척", "되게", "좀더", "정말로",
    "이런", "그런", "저런", "같은", "이상", "다른",
    "하나", "생각", "경우", "정도", "부분", "기준", "수준", "상태",
    "모습", "종류", "방법", "이유", "때문", "번", "개",
    "것들", "느낌", "기분", "편", "때", "곳", "점",
    "구매", "상품", "제품", "물건", "옷", "신발", "가방", "리뷰",
    "후기", "평가", "구입", "주문", "확인", "추가", "배송", "사용",
    "부탁", "감사", "드립", "합니다", "됩니다", "입니다",
    "부탁드립니다", "감사합니다",
    "오늘", "어제", "지금", "나중", "이번", "작년", "다음", "요즘",
    "좋다", "이쁘다", "없다", "있다", "싶다", "어떻다",
}

EXCLAMATION_PATTERN = re.compile(r"^[ㄱ-ㅎㅏ-ㅣ가-힣\s!?~ㅋㅎ\.\,]*$")
PROFANITY_ONLY_PATTERN = re.compile(r"^(씨발|개새끼|병신|ㅅㅂ|ㅂㅅ|존나|ㄷㅊ|지랄)+[\s!?]*$")
EMOTION_PATTERN = re.compile(r"(진짜 최악|돈 아까워요|아깝다|실망|최악|별로|짜증)")

# Kiwi 전역 초기화
try:
    from kiwipiepy import Kiwi
    _kiwi = Kiwi()
except ImportError:
    _kiwi = None


def init_stopwords(brand_names: list[str]) -> None:
    """브랜드명을 불용어에 동적 추가."""
    for name in brand_names:
        STOPWORDS.add(name)


# ---------------------------------------------------------------------------
# 텍스트 유틸
# ---------------------------------------------------------------------------

def normalize_for_keywords(text: str) -> str:
    """동의어를 대표어로 치환 (키워드 카운팅 전용)."""
    for src, tgt in SYNONYM_MAP.items():
        text = text.replace(src, tgt)
    return text


def count_korean_chars(text: str) -> int:
    return sum(1 for ch in text if "가" <= ch <= "힣")


def _kw_counts(text: str) -> tuple[int, int]:
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    return neg, pos


def detect_sentiment(text: str) -> str:
    neg, pos = _kw_counts(text)
    if neg == 0 and pos == 0:
        return "중립"
    if neg > 0 and pos == 0:
        return "부정"
    if pos > 0 and neg == 0:
        return "긍정"
    return "혼합"  # 양쪽 키워드 모두 존재


def is_neg_dominant(text: str) -> bool:
    """혼합 리뷰에서 부정 키워드가 긍정보다 많으면 True."""
    neg, pos = _kw_counts(text)
    return neg > pos


def detect_categories(text: str) -> list[str]:
    norm = normalize_for_keywords(text)
    matched = [
        cat for cat, kws in FEEDBACK_CATEGORIES.items()
        if any(kw in norm for kw in kws)
    ]
    return matched if matched else ["기타"]


def extract_season(val) -> str | None:
    if pd.isna(val):
        return None
    s = str(val).strip().upper()
    return s if s in SEASON_ORDER else None


def similarity_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


# ---------------------------------------------------------------------------
# 제외 조건
# ---------------------------------------------------------------------------

def should_exclude(text: str, categories: list[str]) -> bool:
    if count_korean_chars(text) < 10 and EXCLAMATION_PATTERN.match(text.strip()):
        return True
    if categories == ["기타"]:
        return True
    if PROFANITY_ONLY_PATTERN.match(text.strip()) and not EMOTION_PATTERN.search(text):
        return True
    return False


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates(subset=["BRAND_NAME", "REVIEW_TEXT"], keep="first").copy()
    drop_indices = set()
    for _, group in df.groupby("BRAND_NAME"):
        buckets: dict = {}
        for idx, text in zip(group.index, group["REVIEW_TEXT"]):
            key = (text[:20], len(text) // 10)
            buckets.setdefault(key, []).append((idx, text))
        for candidates in buckets.values():
            if len(candidates) < 2:
                continue
            for i in range(len(candidates)):
                if candidates[i][0] in drop_indices:
                    continue
                for j in range(i + 1, len(candidates)):
                    if candidates[j][0] in drop_indices:
                        continue
                    if similarity_ratio(candidates[i][1], candidates[j][1]) >= 0.9:
                        drop_indices.add(candidates[j][0])
    return df.drop(index=list(drop_indices)).copy()


# ---------------------------------------------------------------------------
# 대표 리뷰 선정
# ---------------------------------------------------------------------------

def score_review(text: str) -> int:
    score = 0
    if re.search(r"\d+\s*(번|cm|일|달|개월|년|회|번째|시간)", text):
        score += 3
    if re.search(r"(반품|환불|재구매 포기|다시는 안 사|다시는 안살)", text):
        score += 3
    if re.search(r"(작년|이전|같은 사이즈|그때|저번)", text):
        score += 2
    if re.search(r"(진짜|완전|절대|실망|돈 아까워요|아깝다|짜증)", text):
        score += 1
    if re.search(r"^(좋아요|별로예요|배송 빠르고 상품 좋아요)$", text.strip()):
        score -= 3
    if len(text) < 30:
        score -= 2
    if len(text) > 300:
        score -= 1  # 너무 긴 리뷰 소폭 감산
    return score


def _cat_kw_count(text: str, cat_name: str) -> int:
    """특정 카테고리의 키워드 히트 수."""
    norm = normalize_for_keywords(text)
    return sum(1 for kw in FEEDBACK_CATEGORIES.get(cat_name, []) if kw in norm)


def _max_other_cat_count(text: str, cat_name: str) -> int:
    """다른 카테고리 중 가장 높은 키워드 히트 수."""
    norm = normalize_for_keywords(text)
    return max(
        (sum(1 for kw in kws if kw in norm)
         for cat, kws in FEEDBACK_CATEGORIES.items() if cat != cat_name),
        default=0,
    )


def filter_primary_cat(rows: pd.DataFrame, cat_name: str) -> pd.DataFrame:
    """해당 카테고리가 주 주제인 리뷰만 남김.
    내 카테고리 키워드 수 >= 다른 카테고리 최다 키워드 수인 행만 통과."""
    def is_primary(text: str) -> bool:
        my_cnt = _cat_kw_count(text, cat_name)
        other_max = _max_other_cat_count(text, cat_name)
        return my_cnt >= other_max  # 동점 포함

    mask = rows["REVIEW_TEXT"].apply(is_primary)
    filtered = rows[mask]
    return filtered if len(filtered) > 0 else rows  # 0건이면 폴백


def _direction_score(text: str, sentiment: str) -> int:
    """감성 방향 일치도 점수: 선정 대상 감성과 일치할수록 높은 점수."""
    neg_cnt = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    pos_cnt = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    if sentiment == "부정":
        return neg_cnt * 2 - pos_cnt
    else:
        return pos_cnt * 2 - neg_cnt


def pick_voices(rows: pd.DataFrame, sentiment: str, cat_name: str, n: int = 5) -> list:
    """긍정 또는 부정 리뷰에서 대표 n개 선정. shoplink 채널은 무조건 제외.
    카테고리 관련성이 높은 리뷰를 우선 선정 (하드 필터 대신 점수 기반)."""
    pool = rows[rows["CHANNEL"].str.lower() != "shoplink"]
    scored = sorted(
        [
            (
                score_review(row["REVIEW_TEXT"])
                + _direction_score(row["REVIEW_TEXT"], sentiment)
                + _cat_kw_count(row["REVIEW_TEXT"], cat_name) * 3
                - _max_other_cat_count(row["REVIEW_TEXT"], cat_name) * 2,
                len(row["REVIEW_TEXT"]),
                row,
            )
            for _, row in pool.iterrows()
        ],
        key=lambda x: (x[0], x[1]),
        reverse=True,
    )
    result = []
    for _, _, row in scored[:n]:
        product_name = row.get("PRODUCT_NAME", "")
        result.append({
            "텍스트": row["REVIEW_TEXT"],
            "상품명": product_name if pd.notna(product_name) else "",
            "시즌": row["시즌"] if pd.notna(row.get("시즌")) else None,
            "채널": row["CHANNEL"],
            "아이템카테고리": row["아이템카테고리"],
        })
    return result


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def process(input_path: str, output_path: str) -> None:
    for enc in ("utf-8-sig", "cp949", "euc-kr"):
        for sep in (",", "\t"):
            try:
                df = pd.read_csv(input_path, encoding=enc, sep=sep)
                if len(df.columns) > 2:
                    break
            except (UnicodeDecodeError, ValueError):
                continue
        else:
            continue
        break
    else:
        raise ValueError(f"CSV 인코딩/구분자 감지 실패: {input_path}")

    # 시즌 컬럼 자동 감지
    season_col = next(
        (c for c in ["브도시즌", "년도시즌", "시즌", "SEASON"] if c in df.columns),
        None,
    )
    if season_col is None:
        raise ValueError(f"시즌 컬럼 없음. 실제 컬럼: {list(df.columns)}")

    for col in ["REVIEW_TEXT", "STYLE_CODE", "CHANNEL"]:
        df[col] = df[col].fillna("").astype(str)

    # 브랜드명 불용어 등록
    brand_names = df["BRAND_NAME"].dropna().unique().tolist()
    init_stopwords(brand_names)

    # STEP 1 — 총 리뷰 수 (필터링 전)
    total_counts = df.groupby("BRAND_NAME").size().to_dict()

    # STEP 2 — 아이템 카테고리 / 시즌
    df["아이템카테고리"] = df.apply(
        lambda r: get_item_category(r["BRAND_NAME"], r["STYLE_CODE"]), axis=1
    )
    df["시즌"] = df[season_col].apply(extract_season)

    # STEP 3 — 카테고리 감지 / 제외 판단
    df["_categories"] = df["REVIEW_TEXT"].apply(detect_categories)
    df["_exclude"] = df.apply(
        lambda r: should_exclude(r["REVIEW_TEXT"], r["_categories"]), axis=1
    )

    # 중복 제거
    valid = remove_duplicates(df[~df["_exclude"]].copy())
    df["_exclude"] = ~df.index.isin(valid.index)

    # 감성 분류
    df["감성"] = df["REVIEW_TEXT"].apply(detect_sentiment)

    brands = sorted(df["BRAND_NAME"].dropna().unique().tolist())
    output: dict = {"brands": brands, "data": {}}

    for brand in brands:
        brand_all = df[df["BRAND_NAME"] == brand]
        brand_valid = brand_all[~brand_all["_exclude"]]

        총리뷰수 = total_counts.get(brand, len(brand_all))
        분석대상 = len(brand_valid)

        items = sorted(brand_valid["아이템카테고리"].dropna().unique().tolist())
        아이템별: dict = {}

        for item in items:
            item_rows = brand_valid[brand_valid["아이템카테고리"] == item]
            item_total = len(item_rows)

            # 아이템 코드 수집 (STYLE_CODE에서 추출)
            is_hufan = (brand == "슈펜")
            raw_codes = item_rows["STYLE_CODE"].apply(
                lambda s: s[2:5] if (is_hufan and len(s) >= 5) else (s[2:4] if len(s) >= 4 else "")
            )
            item_codes = sorted(set(c for c in raw_codes if c))

            cat_list = []
            for cat_name, cat_kws in FEEDBACK_CATEGORIES.items():
                cat_rows = item_rows[
                    item_rows["_categories"].apply(lambda c: cat_name in c)
                ]
                if len(cat_rows) == 0:
                    continue

                # 혼합 리뷰는 우세한 쪽에만 배정 (양쪽 중복 노출 방지)
                pure_neg  = cat_rows[cat_rows["감성"] == "부정"]
                pure_pos  = cat_rows[cat_rows["감성"] == "긍정"]
                mixed     = cat_rows[cat_rows["감성"] == "혼합"]
                mixed_neg = mixed[mixed["REVIEW_TEXT"].apply(is_neg_dominant)]
                mixed_pos = mixed[~mixed["REVIEW_TEXT"].apply(is_neg_dominant)]

                cat_neg = pd.concat([pure_neg, mixed_neg])
                cat_pos = pd.concat([pure_pos, mixed_pos])
                cat_total = len(cat_rows)
                neg_ratio = round(len(cat_neg) / cat_total * 100, 1)

                cat_list.append({
                    "카테고리명": cat_name,
                    "리뷰수": cat_total,
                    "부정비중": neg_ratio,
                    "긍정비중": round(100 - neg_ratio, 1),
                    "대표부정리뷰": pick_voices(cat_neg, "부정", cat_name),
                    "대표긍정리뷰": pick_voices(cat_pos, "긍정", cat_name),
                })

            cat_list.sort(key=lambda x: -x["리뷰수"])

            아이템별[item] = {
                "총리뷰수": item_total,
                "아이템코드": item_codes,
                "피드백카테고리별": cat_list,
            }

        output["data"][brand] = {
            "총리뷰수": 총리뷰수,
            "분석대상리뷰수": 분석대상,
            "아이템목록": items,
            "아이템별": 아이템별,
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"완료: {output_path} ({len(brands)}개 브랜드)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="data.json")
    args = parser.parse_args()
    process(args.input, args.output)
