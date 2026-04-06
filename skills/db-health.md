# DB 건강 점검 에이전트 팀 - PDCA 데이터베이스 최적화

당신은 DB 최적화 전문 에이전트 팀 리더입니다. 2개 전문 에이전트 팀을 **동시에** 출동시켜 **시나리오 매트릭스 + 영향도 맵 + 체크리스트** 기반 PDCA 사이클로 DB 점검 → 최적화 → 재점검을 **90점 이상**까지 자동 반복합니다.

인자: $ARGUMENTS (점검 대상: "전체" 또는 특정 모델/테이블)

---

## Phase 1: PLAN

### 1-1. DB 구조 파악
```bash
cat prisma/schema.prisma
grep -rn "prisma\." src/app/api/ --include="*.ts"
```

### 1-2. DB 영향도 맵

```
📦 DB 영향도 맵
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[테이블 관계 맵]
  Customer ──1:N── Vehicle
  Customer ──1:N── Reservation
  Reservation ──N:1── Vehicle
  Reservation ──1:N── ReservationPart
  ...

[API → 테이블 맵]
  /api/customers → Customer (CRUD)
  /api/reservations → Reservation + Vehicle + Part (복합)
  /api/dashboard → 전 테이블 (읽기 전용 집계)

[쿼리 패턴 맵]
  ├── 단순 조회: findMany (인덱스 필요?)
  ├── 관계 로딩: include (과다?)
  ├── 복합 수정: $transaction (누락?)
  └── 집계 쿼리: aggregate/groupBy (최적화?)

[데이터 흐름 맵]
  생성 → 수정 → 완료(재고차감) → 취소(재고환불) → 삭제
  각 단계에서 영향받는 테이블 표시
```

### 1-3. DB 시나리오 매트릭스

```
X축 (쿼리 유형): findMany | findUnique | create | update | delete | aggregate
Y축 (테이블):   각 모델
Z축 (데이터량):  빈 테이블 | 10건 | 100건 | 1000건+

도출 (최소 20개):
  DB-01: Reservation findMany - 인덱스 없이 1000건 조회
  DB-02: Customer create - 유니크 제약 위반
  DB-03: Reservation update + Part update - 트랜잭션 없이 실행
  DB-04: Dashboard aggregate - 전체 스캔 vs 인덱스 활용
  ...
```

### 1-4. DB 체크리스트

```
━━━ DB 마스터 체크리스트 ━━━
[스키마] (팀1)
  ☐ SCH-01: WHERE 자주 사용 필드에 @@index
  ☐ SCH-02: 복합 인덱스 필요한 쿼리 패턴
  ☐ SCH-03: 유니크 제약 누락
  ☐ SCH-04: onDelete 설정 적절성
  ☐ SCH-05: optional vs required 적절성
  ☐ SCH-06: 미사용 필드/모델

[쿼리] (팀2)
  ☐ QRY-01: N+1 쿼리 (루프 내 prisma 호출)
  ☐ QRY-02: 과다 include (미사용 관계 로딩)
  ☐ QRY-03: select 미사용 (전체 필드 조회)
  ☐ QRY-04: 트랜잭션 누락 (다중 테이블 수정)
  ☐ QRY-05: 인덱스 없는 orderBy
  ☐ QRY-06: skip/take 없는 findMany (대량)
  ☐ QRY-07: 에러 핸들링 누락

각 항목별 영향도 맵 연결 (어떤 API, 어떤 테이블)
```

---

## Phase 2: DO (2팀 동시 출동)

### 팀 1: 스키마 아키텍트 — SCH 체크리스트 담당
영향도 맵의 "테이블 관계 맵"을 따라 스키마 분석.

### 팀 2: 쿼리 최적화반 — QRY 체크리스트 담당
영향도 맵의 "API → 테이블 맵 + 쿼리 패턴 맵"을 따라 쿼리 분석.

---

## Phase 3: CHECK (점수화 + 교차 검증)

### 3-1. 체크리스트 결과 + 커버리지
### 3-2. 교차 검증
- 팀1(인덱스 누락) + 팀2(느린 쿼리) → **인덱스 추가로 쿼리 성능 개선 확인**
- 팀1(관계 설정) + 팀2(include 과다) → **관계는 있지만 불필요 로딩**

### 3-3. 영향도 맵 기반 최적화 리스크
```
SCH-01 인덱스 추가 시:
  → 영향 API: N개 (쓰기 성능 약간 감소)
  → 리스크: 낮음 (읽기 성능 개선)
  
QRY-04 트랜잭션 추가 시:
  → 영향 API: /api/reservations (완료/취소)
  → 리스크: 중간 (기존 동작 변경)
```

### 3-4. 점수화 + 모델별 현황표

---

## Phase 4: ACT → Phase 5: REPORT

수정 순서: N+1 해결 → 인덱스 추가 → select 적용 → 트랜잭션 적용 → 에러 핸들링
스키마 변경 시: prisma validate → generate → db push
보고서: `docs/04-report/db-report-{날짜}.md`
포함: 영향도 맵, 시나리오 매트릭스, 체크리스트 총괄, 쿼리 개선 Before/After, 점수 변화

---

## 핵심 규칙

1. **영향도 맵 필수**: 테이블 관계/API매핑/쿼리패턴/데이터흐름 4가지 추적
2. **시나리오 매트릭스 필수**: 쿼리 유형 × 테이블 × 데이터량 조합
3. **체크리스트 필수**: 13개 항목 전부 실행 + 결과 기록
4. **교차 검증 필수**: 스키마 + 쿼리 결과 교차 분석
5. **스키마 변경 주의**: prisma validate 통과 후에만 적용
6. **PDCA 자동 반복**: 90점 미만 시 최적화 → 재점검 최대 3회
