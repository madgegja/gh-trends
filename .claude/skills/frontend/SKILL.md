---
name: frontend
description: Premium frontend design rules — anti-generic UI, typography, color, layout, interactivity. TRIGGER when creating HTML/CSS/React/Vue/Svelte components, UI mockups, dashboards, or any visual interface. Auto-apply design variance and AI-tell prevention.
---

# Frontend Design Skill

taste-skill, gstack, superpowers에서 추출한 프론트엔드 디자인 규칙 통합본.
프레임워크 무관 (React, Vue, Svelte, vanilla 모두 적용).

## 1. Baseline Configuration

```
DESIGN_VARIANCE: 8   (1=완벽 대칭, 10=아트 카오스)
MOTION_INTENSITY: 6  (1=정적, 10=시네마틱)
VISUAL_DENSITY: 4    (1=갤러리/에어리, 10=대시보드/데이터 팩)
```

사용자 요청에 따라 동적 조정. 기본값은 위 숫자.

## 2. Architecture Rules

- **의존성 검증 [필수]:** 3rd party import 전 반드시 package.json 확인. 없으면 설치 명령 먼저 출력.
- **이모지 금지:** 코드, 마크업, 텍스트, alt text에 이모지 사용 금지. 고품질 아이콘으로 대체.
- **뷰포트:** `h-screen` 금지 → `min-h-[100dvh]` (iOS Safari 대응)
- **Grid > Flex:** `w-[calc(33%-1rem)]` 같은 flex 수학 금지 → CSS Grid 사용
- **컨테이너:** max-width 1200-1440px + auto margin 필수

## 3. Typography

| 규칙 | 금지 | 대신 |
|---|---|---|
| 폰트 | 브라우저 기본, Inter 남용 | Geist, Outfit, Satoshi 등 개성 있는 폰트 |
| 웨이트 | 400/700만 사용 | 500(Medium), 600(SemiBold) 추가 |
| 헤딩 | 작고 평범한 타이틀 | 크게, letter-spacing 타이트, line-height 줄임 |
| 본문 폭 | 제한 없는 텍스트 | max-width ~65ch |
| 숫자 | 비례폰트 | `font-variant-numeric: tabular-nums` |
| 대문자 | ALL CAPS 남용 | sentence case, small-caps |
| 고아 단어 | 마지막 줄 단어 1개 | `text-wrap: balance` |

## 4. Color & Surface

- `#000000` 금지 → off-black (`#0a0a0a`, `#121212`, 틴티드 다크)
- 채도 80% 이하 유지. 과포화 액센트 금지.
- 액센트 컬러 1개만. 나머지 제거.
- 보라/파랑 "AI 그라디언트" 금지 — 가장 흔한 AI 디자인 지문.
- `box-shadow`는 배경 색조에 맞게 틴팅. 순수 검정 그림자 금지.
- 플랫 디자인에 텍스처 추가 (노이즈, 그레인, 미세 패턴).
- 그림자 방향 일관성 (단일 광원).

## 5. Layout

- **3컬럼 동일 카드 금지** — 가장 generic한 AI 레이아웃. 2컬럼 지그재그, 비대칭 그리드, 수평 스크롤로 대체.
- 완벽 대칭 금지 → 오프셋 마진, 비대칭 배치.
- 요소간 깊이감 추가 — negative margin으로 레이어링.
- 상하 패딩 동일 금지 — 하단을 약간 더 크게 (옵티컬 보정).
- 카드 그룹에서 버튼 하단 정렬.
- 가격표/비교 카드에서 피처 리스트 Y좌표 정렬.

## 6. Interactivity & States

- hover 없는 버튼 금지 → background shift, scale, translate
- 즉각 전환 금지 → 200-300ms transition
- pressed 피드백 → `scale(0.98)` or `translateY(1px)`
- focus ring 필수 (키보드 네비게이션)
- 로딩: 스피너 금지 → skeleton loader
- empty state, error state 필수 디자인
- `top/left/width/height` 애니메이션 금지 → `transform + opacity` (GPU 가속)

## 7. AI Tells — 금지 패턴

### 비주얼
- 직선 구분선 (`<hr>`, `border-b`) 남용
- 모든 카드에 동일한 border + shadow + white bg
- 파란 CTA 버튼 + 회색 secondary
- 동일 border-radius 남발

### 콘텐츠
- "John Doe", "Jane Smith" → 다양하고 현실적인 이름
- `99.99%`, `$100.00` → 자연스러운 숫자 (`97.3%`, `$84.50`)
- "Acme Corp", "Nexus" → 맥락에 맞는 브랜드명
- "Elevate", "Seamless", "Unleash", "Next-Gen", "Game-changer" 금지
- Lorem Ipsum 절대 금지
- 느낌표 → 제거. "Oops!" → 직접적 에러 메시지

### 컴포넌트
- 3카드 캐러셀 후기 → masonry wall, 소셜 임베드
- 모든 것에 모달 → inline editing, slide-over, expandable
- FAQ 아코디언 → side-by-side, 검색 가능 도움말
- 아바타 항상 원형 → squircle, rounded square 시도

## 8. Pre-Flight Check

코드 제출 전 반드시 확인:
- [ ] `h-screen` 대신 `min-h-[100dvh]` 사용?
- [ ] 3rd party 라이브러리 설치 명령 포함?
- [ ] 모든 인터랙티브 요소에 hover/active/focus 상태?
- [ ] 금지 패턴(AI tells) 없음?
- [ ] 이모지 없음?
- [ ] 실제 데이터처럼 보이는 더미 데이터?
- [ ] GPU 가속 애니메이션만 사용? (transform, opacity)
