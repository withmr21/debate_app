/**
 * 토론을 통해 AI를 이겨라 - 구글 시트 연동 Apps Script
 * 
 * 사용 방법:
 * 1. 구글 스프레드시트 새로 만들기
 * 2. 메뉴에서 "확장 프로그램 > Apps Script" 열기
 * 3. 기존 코드 모두 지우고 이 코드 전체 붙여넣기
 * 4. Ctrl+S로 저장 (프로젝트 이름은 자유롭게)
 * 5. 좌측 메뉴에서 doPost 함수를 선택 후 "실행" 버튼 클릭
 *    -> 권한 승인 팝업이 뜨면 "고급 > 안전하지 않음으로 이동 > 허용"
 * 6. "배포 > 새 배포" 클릭
 *    -> 유형: 웹 앱
 *    -> 설명: 토론앱 (아무거나)
 *    -> 다음으로 실행: 나
 *    -> 액세스 권한: 모든 사용자  (★★ 매우 중요!)
 * 7. "배포" 클릭 후 나오는 URL 복사 → 토론앱 관리자 설정에 붙여넣기
 * 
 * 코드를 수정했다면 반드시 "배포 > 새 배포" 다시 실행!
 * (저장만 하면 적용 안 됨)
 */

const SHEET_NAME = "토론결과";

function doPost(e) {
  try {
    // 요청 파싱
    let data;
    if (e && e.postData && e.postData.contents) {
      data = JSON.parse(e.postData.contents);
    } else {
      data = {};
    }

    Logger.log("받은 데이터 타입: " + data.type);
    Logger.log("받은 데이터: " + JSON.stringify(data));

    // 시트 가져오기 (없으면 생성)
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName(SHEET_NAME);
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAME);
      // 헤더 작성
      const headers = [
        "기록일시", "유형", "학년", "반", "번호", "이름", 
        "논제", "학생입장", "승자", 
        "논리성", "근거의질", "반박능력", "표현력",
        "소계(40점)", "초과감점", "총점",
        "잘한점", "개선점", "인상적순간", "토론요약",
        "토론기록전문"
      ];
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      sheet.getRange(1, 1, 1, headers.length)
        .setFontWeight("bold")
        .setBackground("#2563eb")
        .setFontColor("#ffffff");
      sheet.setFrozenRows(1);

      // 컬럼 너비 조정
      sheet.setColumnWidth(1, 140);  // 기록일시
      sheet.setColumnWidth(2, 80);   // 유형
      sheet.setColumnWidth(3, 60);   // 학년
      sheet.setColumnWidth(4, 50);   // 반
      sheet.setColumnWidth(5, 50);   // 번호
      sheet.setColumnWidth(6, 80);   // 이름
      sheet.setColumnWidth(7, 300);  // 논제
      sheet.setColumnWidth(8, 80);   // 학생입장
      sheet.setColumnWidth(9, 80);   // 승자
      for (let i = 10; i <= 16; i++) sheet.setColumnWidth(i, 80); // 점수 컬럼들
      sheet.setColumnWidth(17, 400); // 잘한점
      sheet.setColumnWidth(18, 400); // 개선점
      sheet.setColumnWidth(19, 300); // 인상적순간
      sheet.setColumnWidth(20, 400); // 토론요약
      sheet.setColumnWidth(21, 600); // 토론기록전문
    }

    // 데이터 행 추가
    const row = [
      data.timestamp || new Date().toLocaleString("ko-KR"),
      data.type || "",
      data.grade || "",
      data.class || "",
      data.number || "",
      data.name || "",
      data.topic || "",
      data.student_position || "",
      data.winner || "",
      data.logic_score || "",
      data.evidence_score || "",
      data.rebuttal_score || "",
      data.expression_score || "",
      data.subtotal || "",
      data.overtime_penalty || "",
      data.total_score || "",
      data.strengths || "",
      data.improvements || "",
      data.key_moments || "",
      data.summary || "",
      data.debate_log || ""
    ];

    const newRow = sheet.appendRow(row);
    const lastRow = sheet.getLastRow();

    // 가독성을 위한 행 서식 적용
    if (data.type === "debate_result") {
      // 점수 행: 가운데 정렬 + 색상
      sheet.getRange(lastRow, 10, 1, 7).setHorizontalAlignment("center");

      // 텍스트 행: 자동 줄바꿈
      sheet.getRange(lastRow, 17, 1, 5).setWrap(true).setVerticalAlignment("top");

      // 점수 색상 (총점 기준)
      const totalScore = Number(data.total_score) || 0;
      let bgColor = "#ffffff";
      if (totalScore >= 35) bgColor = "#dcfce7";       // 매우 우수 (녹색)
      else if (totalScore >= 28) bgColor = "#dbeafe";  // 우수 (파랑)
      else if (totalScore >= 21) bgColor = "#fef3c7";  // 보통 (노랑)
      else bgColor = "#fee2e2";                         // 미흡 (빨강)

      sheet.getRange(lastRow, 16).setBackground(bgColor).setFontWeight("bold");

      // 행 높이 자동 조정
      sheet.setRowHeight(lastRow, 100);
    } else if (data.type === "test") {
      // 테스트 행은 회색
      sheet.getRange(lastRow, 1, 1, 21).setBackground("#f3f4f6");
    }

    Logger.log("행 추가 완료, 행 번호: " + lastRow);

    return ContentService
      .createTextOutput(JSON.stringify({
        success: true,
        message: "기록 완료",
        row: lastRow
      }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    Logger.log("오류: " + err.toString());
    Logger.log("스택: " + err.stack);
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        error: err.toString(),
        stack: err.stack
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// GET 요청 처리 (브라우저 직접 접속 테스트용)
function doGet(e) {
  return ContentService
    .createTextOutput(JSON.stringify({
      success: true,
      message: "토론앱 웹훅이 정상 작동 중입니다. POST 요청을 보내주세요."
    }))
    .setMimeType(ContentService.MimeType.JSON);
}

// 수동 테스트 함수 (Apps Script 편집기에서 실행 가능)
function testManually() {
  const testData = {
    postData: {
      contents: JSON.stringify({
        type: "test",
        timestamp: new Date().toLocaleString("ko-KR"),
        name: "테스트",
        topic: "수동 테스트"
      })
    }
  };
  const result = doPost(testData);
  Logger.log("결과: " + result.getContent());
}
