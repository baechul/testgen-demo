.PHONY: report report-open report-stop

ALLURE_RESULTS := allure-results
ALLURE_REPORT  := allure-report

report:
	uv run pytest tests --alluredir=$(ALLURE_RESULTS)
	allure generate $(ALLURE_RESULTS) -o $(ALLURE_REPORT) --clean

report-open: report
	allure open $(ALLURE_REPORT)

report-stop:
	-pkill -f "io.qameta.allure" 2>/dev/null || true
