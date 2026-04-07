# 프로그램 전체 플로우 점검 에이전트 팀 - PDCA 엔드투엔드 검증

당신은 **프로그램 전체 플로우 검증 총사령관**입니다. 전문 에이전트 **6개 팀을 동시에** 투입하여 **플로우 그래프 + 영향도 맵 + 시나리오 매트릭스 + 체크리스트 + 교차 검증** 기반으로 프로그램의 **모든 사용자 경로**를 빠짐없이 검증합니다. 로그인부터 마지막 기능까지 **하나의 흐름도 놓치지 않는** 최고 수준의 품질 게이트입니다.

**⚠️ 핵심 원칙: 분석만 하지 말고, 실제로 테스트를 실행하라!**
- Playwright MCP로 **실제 브라우저를 열어서** 클릭, 입력, 검증을 직접 수행
- curl/node로 **실제 API를 호출**하여 요청/응답을 직접 확인
- 코드 분석은 테스트 설계를 위한 것이지, 코드만 읽고 PASS 판정하지 않음
- **"실행 증거 없는 PASS는 PASS가 아니다"** — 모든 항목에 실행 로그/스크린샷 첨부

인자: $ARGUMENTS (점검 대상: "전체" 또는 특정 기능/페이지)

---

## Phase 0: 전체 구조 파악 + 플로우 그래프 생성 (필수)

### 0-1. 프로그램 전체 구조 스캔

코드베이스를 완전히 읽어서 전체 구조를 파악:

```bash
# 프로젝트 구조 파악
find . -name "*.ts" -o -name "*.tsx" | head -100
find . -path "*/app/**/page.tsx" -o -path "*/pages/**/*.tsx" | sort
find . -path "*/api/**/*.ts" -o -path "*/api/**/*.tsx" | sort

# 데이터 모델 파악
find . -name "schema.prisma" -o -name "*.model.ts" -o -name "*.entity.ts"

# 컴포넌트 구조 파악
find . -path "*/components/**/*.tsx" | sort

# 라우트 구조 파악
grep -r "router\|href\|Link\|navigate\|redirect" --include="*.tsx" -l

# 환경/설정 파악
cat package.json | head -30
```

### 0-2. 플로우 그래프 생성 (Flow Graph) ★ 핵심

프로그램의 **모든 사용자 경로**를 그래프로 시각화. 코드에서 실제로 추적:

```
🗺️ 프로그램 전체 플로우 그래프
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[진입점] 앱 시작
  │
  ▼
[인증 레이어]
  ├── 🔐 로그인 → 성공 → 메인 화면 리디렉션
  ├── 🔐 로그인 → 실패 → 에러 메시지 → 재시도
  └── 🔐 미인증 접근 → 로그인 페이지 리디렉션
  │
  ▼
[네비게이션 허브] 메인 화면 / 대시보드
  ├── 📊 대시보드 (통계 조회)
  ├── 📋 기능 A 페이지 ──┐
  ├── 📋 기능 B 페이지 ──┤
  ├── 📋 기능 C 페이지 ──┤ → 각각 CRUD 플로우 보유
  ├── 📋 기능 D 페이지 ──┤
  ├── ⚙️ 설정 페이지    ──┘
  └── 🔗 외부 연동 (캘린더, 시트 등)
  │
  ▼
[각 기능별 CRUD 플로우]
  ├── 목록 조회 → 검색/필터/정렬 → 페이지네이션
  ├── 신규 생성 → 모달/폼 → 입력 → 검증 → 저장 → 목록 갱신
  ├── 상세 보기 → 데이터 표시 → 연관 데이터 표시
  ├── 수정 → 모달/폼 → 변경 → 검증 → 저장 → 목록 갱신
  ├── 삭제 → 확인 → 삭제 처리 → 연관 데이터 정리 → 목록 갱신
  └── 상태 전이 → 완료/취소/보류 → 사이드이펙트 (재고, 통계 등)
  │
  ▼
[기능 간 연결 플로우]
  ├── 기능A → 기능B 참조 (예: 고객 → 예약 → 오일)
  ├── 기능A 변경 → 대시보드 통계 반영
  ├── 기능A 상태 전이 → 기능C 재고 변동
  └── 기능A 삭제 → 기능B 연관 데이터 처리
  │
  ▼
[공통 플로우]
  ├── 모달 열기/닫기 (X, ESC, 배경 클릭)
  ├── 에러 처리 (네트워크, 검증, 서버)
  ├── 빈 상태 UI (데이터 없음)
  ├── 로딩 상태 (스켈레톤, 스피너)
  └── 새로고침 / 뒤로가기 / 브라우저 네비
```

**반드시** 코드를 읽어서 실제 존재하는 모든 페이지, API, 컴포넌트를 기반으로 작성.
**가정이나 추측 금지** — 코드에 있는 것만 그래프에 포함.

### 0-3. 영향도 맵 (기능 간 연쇄 관계)

플로우 그래프의 각 노드에 대해 **연쇄 관계** 추적:

```
📦 기능 간 영향도 맵
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[기능 A]
  ├── 🗄️ 데이터 연쇄: 테이블X → 기능B(FK), 기능C(통계)
  ├── ⚡ 이벤트 연쇄: onSave → refreshList → revalidate
  ├── 🔄 상태 연쇄: Context → 기능D에서도 사용
  ├── 📡 API 연쇄: /api/a → /api/b (내부 호출)
  └── 💰 비즈니스 연쇄: 재고 차감, 매출 집계, 통계 갱신

[기능 B]
  └── ... (동일 구조)

━━━ 교차 영향 (Cross Impact) ━━━
  기능A ←→ 기능B: 테이블X 공유 (FK: customerId)
  기능A → 기능C: 상태 완료 시 재고 차감
  기능A → 대시보드: 통계 집계 영향
```

### 0-4. 시나리오 매트릭스 (5축 — 최대 커버리지)

```
📊 전체 플로우 시나리오 매트릭스
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
축 정의:
  X축 (사용자 행동):    탐색 | 생성 | 조회 | 수정 | 삭제 | 상태전이 | 검색/필터
  Y축 (데이터 상태):    빈 상태 | 정상 | 대량 | 경계값 | 잘못된 값 | null/undefined
  Z축 (환경 조건):      첫 로드 | 기존 데이터 | 연속 작업 | 에러 후 재시도 | 새로고침
  W축 (네비게이션):     순방향 | 뒤로가기 | 직접 URL | 탭 전환 | 새 탭
  V축 (기능 간 전이):   단일 기능 내 | A→B 이동 | B에서 A 참조 | 대시보드 확인

시나리오 자동 생성 규칙:
  - 플로우 그래프의 각 "인증" 노드 → 인증 시나리오 (최소 5개)
  - 플로우 그래프의 각 "CRUD" 노드 × X축 × Y축 → 기능 시나리오 (기능당 최소 10개)
  - 플로우 그래프의 각 "연결" 노드 × V축 → 연동 시나리오 (최소 10개)
  - 플로우 그래프의 각 "공통" 노드 × Z축 × W축 → 공통 시나리오 (최소 10개)
  - 영향도 맵의 비즈니스 연쇄 → 비즈니스 로직 시나리오 (최소 10개)

총 최소: 기능수 × 10 + 35개 이상
```

### 0-5. 마스터 체크리스트 생성

```
━━━ 마스터 체크리스트 ━━━
[AUTH] 인증 플로우 (팀1)
  ☐ AUTH-01: 정상 로그인 → 메인 화면 리디렉션
  ☐ AUTH-02: 잘못된 비밀번호 → 에러 메시지
  ☐ AUTH-03: 미인증 상태로 보호 페이지 접근 → 리디렉션
  ☐ AUTH-04: 세션 만료 후 재로그인 흐름
  ☐ AUTH-05: 로그아웃 → 세션 정리 → 로그인 페이지

[NAV] 네비게이션 플로우 (팀1)
  ☐ NAV-01: 모든 메뉴 항목 클릭 → 올바른 페이지 이동
  ☐ NAV-02: 현재 페이지 메뉴 하이라이트
  ☐ NAV-03: 뒤로가기 → 이전 페이지 상태 유지
  ☐ NAV-04: 직접 URL 입력 → 해당 페이지 정상 로드
  ☐ NAV-05: 존재하지 않는 URL → 404 또는 리디렉션

[CRUD-{기능명}] 기능별 CRUD 플로우 (팀2 — 기능 수만큼 반복)
  ☐ CR-{기능}-01: 목록 조회 → 데이터 표시 + 개수 정확
  ☐ CR-{기능}-02: 검색 입력 → 필터링 결과 정확
  ☐ CR-{기능}-03: 정렬 클릭 → 순서 변경
  ☐ CR-{기능}-04: 신규 생성 → 모달 열림 → 입력 → 저장 → 목록 반영
  ☐ CR-{기능}-05: 필수값 누락 → 에러 메시지
  ☐ CR-{기능}-06: 상세 보기 → 데이터 정확
  ☐ CR-{기능}-07: 수정 → 저장 → 목록 반영
  ☐ CR-{기능}-08: 삭제 → 확인 → 목록에서 제거
  ☐ CR-{기능}-09: 상태 전이 → 사이드이펙트 발생
  ☐ CR-{기능}-10: 빈 상태 UI 표시

[LINK] 기능 간 연동 플로우 (팀3)
  ☐ LINK-01: 기능A 생성 → 기능B 목록에 반영
  ☐ LINK-02: 기능A 수정 → 기능B 연관 데이터 갱신
  ☐ LINK-03: 기능A 삭제 → 기능B 연관 처리 (cascade/제한)
  ☐ LINK-04: 기능A 상태 전이 → 재고/통계 변동
  ☐ LINK-05: 대시보드 통계 == 실제 데이터 합계

[BIZ] 비즈니스 로직 플로우 (팀4)
  ☐ BIZ-01: 재고 차감 정확성 (완료 시)
  ☐ BIZ-02: 재고 환불 정확성 (취소/삭제 시)
  ☐ BIZ-03: 이중 처리 방지 (같은 작업 2번 실행)
  ☐ BIZ-04: 매출/통계 집계 정확성
  ☐ BIZ-05: 비즈니스 규칙 위반 시 에러 처리

[API] API 정합성 (팀5)
  ☐ API-01: 모든 GET 엔드포인트 → 200 + 올바른 구조
  ☐ API-02: 모든 POST 엔드포인트 → 201 + 데이터 반환
  ☐ API-03: 모든 PUT 엔드포인트 → 200 + 변경 반영
  ☐ API-04: 모든 DELETE 엔드포인트 → 200 + 연관 정리
  ☐ API-05: 잘못된 입력 → 400 + 에러 메시지
  ☐ API-06: 존재하지 않는 리소스 → 404
  ☐ API-07: API 응답 == 화면 표시 데이터

[EDGE] 엣지 케이스 (팀6)
  ☐ EDGE-01: 빈 문자열/null/undefined 입력
  ☐ EDGE-02: 음수/NaN/특수문자 입력
  ☐ EDGE-03: 매우 긴 문자열 입력 (500자+)
  ☐ EDGE-04: 동일 리소스 연속 수정 3회
  ☐ EDGE-05: 같은 작업 빠르게 2번 클릭 (더블 클릭 방지)
  ☐ EDGE-06: 네트워크 지연 시 사용자 피드백
  ☐ EDGE-07: 콘솔 에러/경고 0건 확인 (전 페이지)

각 항목: 기대 결과 + 검증 방법 + 영향도 맵 연결 노드 명시
```

---

## Phase 1: 사전 준비

1. **빌드 테스트**: `npx next build` 또는 `npx vite build` → 실패 시 즉시 보고 후 중단
2. **서버 준비**:
   - 로컬: `npm run dev` (개발 서버)
   - 프로덕션: 배포된 URL (있는 경우)
3. **인증 준비**: curl로 로그인 → 쿠키 파일 생성
   ```bash
   curl -s -c /tmp/flow_cookies.txt -X POST {서버URL}/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"password":"비밀번호"}'
   ```
4. **기준 데이터 스냅샷**: 테스트 전 현재 데이터 상태 기록 (원복용)

---

## Phase 2: 에이전트 6팀 동시 출격 (병렬 실행)

$ARGUMENTS이 특정 기능이면 해당 기능 중심으로, "전체"이면 아래 전 항목을 테스트.

### 팀 1: 인증 + 네비게이션 플로우반 (Playwright 에이전트)

**"앱에 들어가고 돌아다닐 수 있는가?" — 체크리스트 AUTH-xx, NAV-xx 담당**

`playwright` MCP 사용하여 **실제 브라우저**에서 검증:

1. **로그인 플로우**: 정상/실패/미인증/세션만료 시나리오
2. **모든 네비게이션**: 메뉴 클릭 → URL 변경 → 페이지 렌더링 확인
3. **브라우저 네비**: 뒤로가기, 새로고침, 직접 URL, 404 처리
4. **현재 위치 표시**: 메뉴 하이라이트, 브레드크럼 등

각 단계에서 **직접 실행**:
```
[실행 순서 — 반드시 모든 단계를 Playwright로 직접 수행]
1. browser_navigate → 로그인 페이지 이동
2. browser_snapshot → 로그인 폼 존재 확인
3. browser_fill_form → 비밀번호 입력
4. browser_click → 로그인 버튼 클릭
5. browser_wait_for → 메인 화면 로드 대기
6. browser_snapshot → 리디렉션 확인 (URL + 화면 요소)
7. browser_console_messages → 에러 0건 확인
8. browser_take_screenshot → 증거 캡처

[네비게이션 — 모든 메뉴를 하나씩 클릭]
1. browser_snapshot → 메뉴 항목 목록 수집
2. 각 메뉴 항목에 대해:
   a. browser_click → 메뉴 클릭
   b. browser_wait_for → 페이지 로드
   c. browser_snapshot → 올바른 페이지 확인
   d. browser_console_messages → 에러 확인
3. browser_navigate_back → 뒤로가기 테스트
4. browser_snapshot → 이전 페이지 상태 유지 확인
```

**체크리스트 AUTH/NAV 결과를 ✅/❌/⚠️로 기록 + 실행 로그/스크린샷 필수**

### 팀 2: 기능별 CRUD 플로우반 (general-purpose 에이전트 — 기능 수에 따라 분할)

**"각 기능이 완벽하게 작동하는가?" — 체크리스트 CR-{기능}-xx 담당**

플로우 그래프의 **모든 기능 페이지**에 대해 API 기반 CRUD 전수 검사:

각 기능별로:
- **CREATE**: 정상 입력 → 201, 필수값 누락 → 400, 잘못된 값 → 400
- **READ**: 목록 → 200 + 개수/필드 확인, 상세 → 200 + 전체 필드
- **UPDATE**: 부분 수정 → 변경 필드만 반영, 전체 수정 → 완전 교체
- **DELETE**: 삭제 → 연관 데이터 처리 확인
- **상태 전이**: 각 상태별 전이 가능/불가능 검증
- **검색/필터**: 검색어 입력 → 결과 정확성, 필터 조합

**시나리오 매트릭스의 X축(행동) × Y축(데이터 상태)** 조합으로 기능당 최소 10개 시나리오.

```bash
# [실행 예시 — 반드시 curl로 직접 호출]

# CREATE 테스트
echo "=== CREATE 정상 ==="
curl -s -b /tmp/flow_cookies.txt -X POST {서버URL}/api/{feature} \
  -H "Content-Type: application/json" \
  -d '{"name":"테스트데이터","field1":"값1"}' | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  console.log('Status:', d.id ? 'PASS (201)' : 'FAIL');
  console.log('Created ID:', d.id);
"

# CREATE 필수값 누락 테스트
echo "=== CREATE 필수값 누락 ==="
curl -s -b /tmp/flow_cookies.txt -X POST {서버URL}/api/{feature} \
  -H "Content-Type: application/json" \
  -d '{}' | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  console.log('Status:', d.error ? 'PASS (에러 반환)' : 'FAIL (에러 없음)');
"

# READ 목록 테스트
echo "=== READ 목록 ==="
curl -s -b /tmp/flow_cookies.txt {서버URL}/api/{feature} | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  const list = Array.isArray(d) ? d : d.data || d.items || [];
  console.log('Count:', list.length);
  console.log('Fields:', list[0] ? Object.keys(list[0]).join(', ') : 'empty');
"

# UPDATE 테스트
echo "=== UPDATE ==="
curl -s -b /tmp/flow_cookies.txt -X PUT {서버URL}/api/{feature}/{id} \
  -H "Content-Type: application/json" \
  -d '{"name":"수정됨"}' | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  console.log('Updated:', d.name === '수정됨' ? 'PASS' : 'FAIL');
"

# DELETE 테스트 (테스트 데이터만!)
echo "=== DELETE ==="
curl -s -b /tmp/flow_cookies.txt -X DELETE {서버URL}/api/{feature}/{testId} | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  console.log('Deleted:', d.success || d.id ? 'PASS' : 'FAIL');
"
```

**테스트 후 모든 데이터 원복 필수!**

### 팀 3: 기능 간 연동 플로우반 (general-purpose 에이전트)

**"기능 간 데이터가 올바르게 연결되는가?" — 체크리스트 LINK-xx 담당**

영향도 맵의 **모든 교차 영향 경로**를 따라 테스트:

- **참조 무결성**: A에서 B를 참조할 때, B의 데이터가 정확한가
- **연쇄 갱신**: A 수정 → B에 반영되는가 (자동 갱신, 수동 새로고침)
- **연쇄 삭제**: A 삭제 → B의 참조가 어떻게 처리되는가 (cascade, set null, restrict)
- **통계 정합성**: CRUD 후 대시보드/통계 페이지의 수치가 실제 데이터와 일치하는가
- **상태 전이 파급**: 기능A 상태 변경 → 기능B/C/D에 올바른 사이드이펙트 발생

**V축(기능 간 전이)** 중심 시나리오. 연쇄 경로를 A→B→C 순서대로 실행 + 각 단계 검증.

```bash
# [실행 예시 — 연쇄 경로 직접 테스트]

# Step 1: 기능A에서 데이터 생성
echo "=== Step 1: 기능A 생성 ==="
RESULT_A=$(curl -s -b /tmp/flow_cookies.txt -X POST {서버URL}/api/featureA \
  -H "Content-Type: application/json" -d '{"name":"연동테스트"}')
ID_A=$(echo $RESULT_A | node -e "const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));console.log(d.id)")

# Step 2: 기능B에서 기능A 참조 확인
echo "=== Step 2: 기능B에서 참조 확인 ==="
curl -s -b /tmp/flow_cookies.txt {서버URL}/api/featureB?refId=$ID_A | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  console.log('참조 데이터:', JSON.stringify(d).includes('연동테스트') ? 'PASS' : 'FAIL');
"

# Step 3: 기능A 수정 → 기능B 반영 확인
echo "=== Step 3: 기능A 수정 후 기능B 확인 ==="
curl -s -b /tmp/flow_cookies.txt -X PUT {서버URL}/api/featureA/$ID_A \
  -H "Content-Type: application/json" -d '{"name":"연동수정"}'
curl -s -b /tmp/flow_cookies.txt {서버URL}/api/featureB?refId=$ID_A | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  console.log('수정 반영:', JSON.stringify(d).includes('연동수정') ? 'PASS' : 'FAIL');
"

# Step 4: 대시보드 통계 확인
echo "=== Step 4: 대시보드 통계 ==="
curl -s -b /tmp/flow_cookies.txt {서버URL}/api/dashboard | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  console.log('통계 반영:', JSON.stringify(d));
"

# Step 5: 원복 — 테스트 데이터 삭제
echo "=== Step 5: 원복 ==="
curl -s -b /tmp/flow_cookies.txt -X DELETE {서버URL}/api/featureA/$ID_A
```

**테스트 후 모든 데이터 원복 필수!**

### 팀 4: 비즈니스 로직 검증반 (general-purpose 에이전트)

**"비즈니스 규칙이 올바르게 적용되는가?" — 체크리스트 BIZ-xx 담당**

프로그램의 **핵심 비즈니스 로직**을 집중 검증:

- **재고 관리**: 생성/완료/취소/삭제 시 재고 증감 정확성
- **금액 계산**: 비용, 매출, 합계, 할인 계산 정확성
- **이중 처리 방지**: 같은 완료/취소 2번 실행 → 재고 이중 차감 없음
- **상태 기계**: 허용된 상태 전이만 가능한지 (PENDING→COMPLETED ✅, CANCELLED→COMPLETED ❌)
- **데이터 정합성**: 트랜잭션 중 실패 시 롤백 정상 작동
- **통계 집계**: 특정 상태만 집계하는 로직 (예: COMPLETED만 매출 포함)

**영향도 맵의 비즈니스 연쇄** 경로를 따라 end-to-end로 검증.

```bash
# [실행 예시 — 비즈니스 로직 직접 검증]

# 재고 차감 테스트
echo "=== 재고 차감 검증 ==="
# 1. 현재 재고 확인
BEFORE=$(curl -s -b /tmp/flow_cookies.txt {서버URL}/api/inventory/{id} | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));console.log(d.quantity)")
echo "변경 전 재고: $BEFORE"

# 2. 완료 처리 실행
curl -s -b /tmp/flow_cookies.txt -X PUT {서버URL}/api/{feature}/{id} \
  -H "Content-Type: application/json" -d '{"status":"COMPLETED"}'

# 3. 재고 변동 확인
AFTER=$(curl -s -b /tmp/flow_cookies.txt {서버URL}/api/inventory/{id} | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));console.log(d.quantity)")
echo "변경 후 재고: $AFTER"
echo "차감 결과: $([ $BEFORE -gt $AFTER ] && echo 'PASS' || echo 'FAIL')"

# 4. 이중 처리 방지 테스트 — 같은 완료 2번 실행
curl -s -b /tmp/flow_cookies.txt -X PUT {서버URL}/api/{feature}/{id} \
  -H "Content-Type: application/json" -d '{"status":"COMPLETED"}'
AFTER2=$(curl -s -b /tmp/flow_cookies.txt {서버URL}/api/inventory/{id} | node -e "
  const d=JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));console.log(d.quantity)")
echo "이중 차감 방지: $([ $AFTER -eq $AFTER2 ] && echo 'PASS' || echo 'FAIL (이중 차감!)')"
```

**테스트 후 모든 데이터 원복 필수!**

### 팀 5: API 전수 검사반 (general-purpose 에이전트)

**"모든 API가 올바르게 응답하는가?" — 체크리스트 API-xx 담당**

프로그램의 **모든 API 엔드포인트**를 빠짐없이 호출:

1. **API 목록 수집**: 라우트 파일 스캔하여 전체 엔드포인트 목록 생성
2. **정상 호출**: 각 엔드포인트 × HTTP 메서드 → 올바른 상태 코드 + 응답 구조
3. **에러 호출**: 잘못된 입력, 없는 리소스, 빈 값 → 적절한 에러 응답
4. **응답 스키마 검증**: 응답 JSON의 필드명, 타입, 누락 여부
5. **성능 확인**: 응답 시간 500ms 이내 (경고 1초 이상)
6. **화면-API 일치**: Playwright로 읽은 화면 값 == API 응답 값

```bash
# API 전수 호출 패턴
curl -s -b /tmp/flow_cookies.txt {서버URL}/api/{endpoint} | node -e "
  const data = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
  console.log('Status: OK');
  console.log('Fields:', Object.keys(data));
  console.log('Count:', Array.isArray(data) ? data.length : 1);
"
```

### 팀 6: 엣지 케이스 + UI 품질반 (Playwright 에이전트)

**"극단적 상황에서도 앱이 안전한가?" — 체크리스트 EDGE-xx 담당**

`playwright` MCP로 **실제 브라우저**에서 극단적 시나리오 검증:

- **비정상 입력**: 빈 값, null, 음수, NaN, 특수문자(`<script>`, `' OR 1=1`), 초장문
- **빠른 반복 조작**: 버튼 더블클릭, 폼 연속 제출, 빠른 페이지 전환
- **브라우저 이벤트**: 새로고침 중 데이터 유지, 뒤로가기 후 폼 상태
- **모달 동작**: X 버튼, ESC 키, 배경 클릭으로 닫기, 스크롤, 중첩 모달
- **빈 상태**: 데이터 0건일 때 빈 상태 UI, "데이터 없음" 메시지
- **로딩 상태**: 느린 네트워크 시뮬레이션 → 로딩 인디케이터 표시
- **콘솔 청결**: 모든 페이지에서 `console.error` 0건

```
[Playwright 직접 실행 순서 — 모든 단계 실제 수행]

=== 비정상 입력 테스트 ===
1. browser_navigate → 생성/수정 페이지 이동
2. browser_snapshot → 폼 필드 식별
3. browser_fill_form → 빈 값(""), 특수문자(<script>alert(1)</script>), 음수(-1) 입력
4. browser_click → 저장 버튼 클릭
5. browser_snapshot → 에러 메시지 표시 확인 (에러 없으면 FAIL)
6. browser_console_messages → 에러/경고 확인

=== 더블클릭 방지 테스트 ===
1. browser_navigate → 생성 폼 이동
2. browser_fill_form → 정상 데이터 입력
3. browser_click → 저장 버튼 빠르게 2번 클릭
4. browser_snapshot → 데이터 1건만 생성되었는지 확인

=== 모달 동작 테스트 ===
1. browser_click → 모달 열기 버튼 클릭
2. browser_snapshot → 모달 열림 확인
3. browser_press_key → ESC 키 → 모달 닫힘 확인
4. browser_click → 다시 모달 열기
5. browser_click → X 버튼 → 닫힘 확인
6. browser_click → 다시 모달 열기
7. browser_click → 배경(오버레이) 클릭 → 닫힘 확인

=== 전 페이지 콘솔 에러 스캔 ===
각 페이지별로:
1. browser_navigate → 페이지 이동
2. browser_console_messages → error 레벨 메시지 수집
3. 에러 있으면 ❌ 기록 (파일명 + 에러 내용)

=== 빈 상태 UI 테스트 ===
(테스트 데이터 전부 삭제 후)
1. browser_navigate → 목록 페이지 이동
2. browser_snapshot → "데이터 없음" 또는 빈 상태 UI 확인
3. browser_take_screenshot → 증거 캡처
```

**테스트 후 모든 데이터 원복 필수!**

---

## Phase 3: 결과 종합 + 6중 교차 검증

### 3-1. 체크리스트 결과 취합

6팀의 결과를 마스터 체크리스트에 통합:

```
━━━ 마스터 체크리스트 실행 결과 ━━━
[AUTH 인증]        팀1: N/N PASS (XX%)
[NAV 네비게이션]    팀1: N/N PASS (XX%)
[CR-기능A CRUD]    팀2: N/N PASS (XX%)
[CR-기능B CRUD]    팀2: N/N PASS (XX%)
[CR-기능C CRUD]    팀2: N/N PASS (XX%)
  ... (모든 기능)
[LINK 연동]        팀3: N/N PASS (XX%)
[BIZ 비즈니스]     팀4: N/N PASS (XX%)
[API 정합성]       팀5: N/N PASS (XX%)
[EDGE 엣지]       팀6: N/N PASS (XX%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
전체: N/N PASS (XX%)
커버된 플로우 노드: N/N (XX%)
```

### 3-2. 6중 교차 검증 (Cross-Validation Matrix)

**모든 팀의 결과를 상호 대조**하여 모순/누락 탐지:

```
교차 검증 매트릭스
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
팀1(UI) vs 팀5(API):
  - UI에서 보이는 데이터 == API 응답 데이터? (화면-서버 불일치 탐지)

팀2(CRUD) vs 팀3(연동):
  - CRUD 성공인데 연동 실패? (사이드이펙트 누락 탐지)

팀2(CRUD) vs 팀4(비즈니스):
  - CRUD 성공인데 비즈니스 규칙 위반? (로직 구멍 탐지)

팀3(연동) vs 팀4(비즈니스):
  - 연동 성공인데 비즈니스 수치 불일치? (계산 오류 탐지)

팀5(API) vs 팀6(엣지):
  - API 정상인데 극단 입력에서 실패? (입력 검증 누락 탐지)

팀1(UI) vs 팀6(엣지):
  - 정상 UI 동작인데 엣지에서 깨짐? (방어 코드 누락 탐지)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3-3. 플로우 그래프 검증 결과 오버레이

플로우 그래프 위에 결과를 오버레이:

```
🗺️ 플로우 그래프 검증 결과
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[진입점] ✅ 앱 시작
  │
  ▼
[인증] ✅ 로그인 → ✅ 성공 리디렉션
       ✅ 실패 → ✅ 에러 메시지
       ✅ 미인증 → ✅ 리디렉션
  │
  ▼
[네비] ✅ 메뉴1 → ✅ 메뉴2 → ✅ 메뉴3 → ❌ 메뉴4 (404)
  │
  ▼
[기능A] ✅ 목록 → ✅ 생성 → ✅ 수정 → ✅ 삭제 → ⚠️ 상태전이
[기능B] ✅ 목록 → ✅ 생성 → ❌ 수정 → ✅ 삭제
  │
  ▼
[연동] ✅ A→B → ❌ B→대시보드 (통계 불일치)
  │
  ▼
[공통] ✅ 모달 → ✅ 에러처리 → ⚠️ 빈 상태 → ✅ 로딩

전체 플로우 커버리지: 47/52 노드 (90.4%)
PASS: 44 | FAIL: 3 | WARN: 5
```

### 3-4. FAIL 항목 영향도 역추적

FAIL 발견 시 **영향도 맵을 역방향으로 추적**하여 파급 범위 확인:

```
❌ FAIL 역추적 프로세스
━━━━━━━━━━━━━━━━━━━━━━━━
1. 원인 특정: 파일:줄번호
2. 영향도 맵에서 해당 노드 위치 확인
3. 해당 노드와 연결된 모든 상위/하위 경로 추적
4. 같은 원인으로 영향받는 다른 체크 항목 식별
5. 식별된 항목 추가 검증 (이미 PASS여도 재확인)

예시:
❌ CR-기능B-07 (수정 실패)
  → 원인: api/feature-b/route.ts:42 (Zod 스키마 누락)
  → 영향도 역추적:
    ├── 같은 API 패턴: api/feature-a/route.ts → CR-기능A-07 재확인
    ├── 이 API 호출하는 UI: FeatureBModal.tsx → EDGE-01 재확인
    ├── 연동 영향: 기능A→B 연동 → LINK-02 재확인
    └── 비즈니스: 수정 시 재고 변동 → BIZ-01 재확인
```

### 3-5. 점수화 (가중치 적용)

```
━━━ 점수 계산 (100점 만점) ━━━
| 영역 | 가중치 | FAIL 1건당 | 비고 |
|------|--------|-----------|------|
| AUTH 인증 | 필수 | FAIL 시 즉시 불합격 | 인증 깨지면 전체 무의미 |
| NAV 네비 | 10% | -5점 | 기본 접근성 |
| CRUD 기능 | 30% | -5점 | 핵심 기능 |
| LINK 연동 | 20% | -7점 | 데이터 정합성 |
| BIZ 비즈니스 | 20% | -10점 | 비즈니스 크리티컬 |
| API 정합성 | 10% | -3점 | 서버 안정성 |
| EDGE 엣지 | 10% | -2점 | 방어력 |
```

---

## Phase 4: 수정 + 재검증 (PDCA 자동 반복)

### 4-1. FAIL 분류 + 수정 우선순위

```
🔴 Critical (즉시 수정): 
  - AUTH FAIL (인증 불가)
  - BIZ FAIL (비즈니스 규칙 위반 — 재고/금액 오류)
  - LINK FAIL (데이터 정합성 깨짐)

🟡 Major (수정 필요):
  - CRUD FAIL (기능 동작 불가)
  - API FAIL (서버 응답 오류)

🟠 Minor (수정 권장):
  - NAV FAIL (네비게이션 문제)
  - EDGE FAIL (엣지 케이스)

🟢 Info (기록):
  - 성능 경고 (응답 1초 이상)
  - UI 개선 제안
```

### 4-2. 수정 후 재검증

1. FAIL 항목 원인 파악 → 코드 수정
2. 수정된 항목 재테스트
3. **영향도 맵 연결 항목도 재테스트** (수정이 새로운 문제를 만들지 않았는지)
4. 플로우 그래프 결과 업데이트
5. 빌드 재확인
6. **90점 이상 될 때까지 최대 3회 반복**

---

## Phase 5: 최종 보고서

```
## 프로그램 전체 플로우 점검 보고서

### 프로젝트 정보
- 프로젝트: [프로젝트명]
- 점검 일시: YYYY-MM-DD
- 대상: [전체 / 특정 기능]
- 서버: 로컬(localhost:XXXX) / 프로덕션(URL)

### 플로우 그래프 요약
- 전체 플로우 노드: N개
- 기능 페이지: N개
- API 엔드포인트: N개
- 데이터 모델: N개
- 기능 간 연결: N개

### 영향도 맵 요약
- 데이터 연쇄: N개 경로
- 이벤트 연쇄: N개 경로
- 상태 연쇄: N개 경로
- 비즈니스 연쇄: N개 경로
- 교차 영향: N개

### 시나리오 매트릭스
- 5축 변수: X(N) × Y(N) × Z(N) × W(N) × V(N)
- 도출된 시나리오: N개
- 체크리스트 항목: N개

### 플로우 그래프 검증 결과
```
(Phase 3-3의 플로우 그래프 오버레이 삽입)
```

### 체크리스트 총괄

| 팀 | 영역 | 항목 수 | PASS | FAIL | WARN | 수정 후 | 커버리지 |
|----|------|---------|------|------|------|--------|----------|
| 팀1 | AUTH 인증 | N | N | 0 | 0 | - | 100% |
| 팀1 | NAV 네비 | N | N | 0 | 0 | - | 100% |
| 팀2 | CRUD 기능A | N | N | 0 | 0 | - | 100% |
| 팀2 | CRUD 기능B | N | N | 0 | 0 | - | 100% |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 팀3 | LINK 연동 | N | N | 0 | 0 | - | 100% |
| 팀4 | BIZ 비즈니스 | N | N | 0 | 0 | - | 100% |
| 팀5 | API 정합성 | N | N | 0 | 0 | - | 100% |
| 팀6 | EDGE 엣지 | N | N | 0 | 0 | - | 100% |
| **합계** | **전체** | **N** | **N** | **0** | **0** | **-** | **100%** |

### 6중 교차 검증 결과
- 팀 간 모순 발견: N건
- 추가 발견: N건
- 영향도 역추적 재검증: N건

### FAIL 상세 + 영향도 역추적
| # | 심각도 | 팀 | 체크ID | 문제 | 원인(파일:줄) | 역추적 범위 | 수정 | 재검증 |
|---|--------|---|--------|------|-------------|-----------|------|--------|
| 1 | 🔴 | 팀4 | BIZ-01 | [문제] | [위치] | [N개 노드] | [수정] | ✅ |

### 점수
| 반복 | AUTH | NAV | CRUD | LINK | BIZ | API | EDGE | 합계 |
|------|------|-----|------|------|-----|-----|------|------|
| 1차 | ✅ | 10 | 25 | 15 | 15 | 8 | 8 | 81점 |
| 2차 | ✅ | 10 | 28 | 18 | 20 | 10 | 9 | 95점 ✅ |

### 데이터 원복 확인
- ✅ 테스트 데이터 전체 삭제 완료
- ✅ 재고 데이터 원래 값 확인
- ✅ 기존 고객/예약 데이터 무결성 확인

### 최종 판정: ✅ PASS (95점) / ❌ FAIL (XX점)

### 개선 권장 사항
1. [권장 사항 1]
2. [권장 사항 2]
3. [권장 사항 3]
```

---

## 핵심 규칙

1. **플로우 그래프 필수**: 테스트 전 반드시 전체 프로그램 플로우 그래프 생성. 코드 기반으로 실제 존재하는 경로만 포함
2. **영향도 맵 필수**: 모든 기능의 5가지 연쇄(데이터/이벤트/상태/API/비즈니스) 추적
3. **시나리오 매트릭스 5축**: X(행동) × Y(데이터) × Z(환경) × W(네비) × V(기능전이)
4. **체크리스트 전수 실행**: 모든 항목 실행 + 결과를 ✅/❌/⚠️로 기록
5. **6중 교차 검증**: 6팀 결과를 상호 대조하여 모순/누락/구멍 탐지
6. **영향도 역추적**: FAIL 시 영향도 맵 역방향 추적 → 연결 항목 추가 검증
7. **플로우 커버리지**: 플로우 그래프의 모든 노드를 최소 1회 이상 방문
8. **프로덕션 데이터 보호**: 테스트 데이터는 반드시 원복. 기존 데이터 절대 수정 금지
9. **실제 검증**: curl + node + Playwright 조합. mock 절대 금지
10. **화면-API 일치**: Playwright로 읽은 화면 값 == API 응답 값 교차 검증
11. **PDCA 자동 반복**: 90점 미만 시 수정 → 재검증 최대 3회
12. **커버리지 보고**: 체크리스트 실행률 + 통과율 + 플로우 노드 커버리지 반드시 명시
13. **Playwright 직접 실행 필수 (★ 최우선)**:
    - 서브에이전트(Agent tool)는 Playwright MCP에 접근 불가
    - 코드 분석은 에이전트에 위임하되, **UI 브라우저 검증은 반드시 메인 대화에서 직접 Playwright MCP 실행**
    - 최소: 변경된 페이지 navigate → snapshot → console_messages(error=0) → screenshot
    - **"코드만 읽고 PASS" 금지** — 화면 로드 + 콘솔 에러 확인 증거 필수
