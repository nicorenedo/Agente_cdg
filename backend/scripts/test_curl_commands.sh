#!/bin/bash

# Script de pruebas cURL para Chart Endpoints V4.4
# Ubicación: backend/scripts/test_curl_commands.sh

BASE_URL="http://127.0.0.1:8000"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="backend/scripts/curl_test_results_${TIMESTAMP}.log"

echo "🚀 Chart Endpoints V4.4 - Pruebas cURL" | tee "$LOG_FILE"
echo "🌐 Base URL: $BASE_URL" | tee -a "$LOG_FILE"
echo "📝 Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "===========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Función helper para logging
log_test() {
    echo "[$( date '+%H:%M:%S' )] $1" | tee -a "$LOG_FILE"
}

# Test 1: Health Check
log_test "🏥 Testing Health Check..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X GET "$BASE_URL/health" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 2: Chart Generator Validation
log_test "🔧 Testing Chart Generator Validation..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X GET "$BASE_URL/admin/validate-chart-generator" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 3: Charts Meta - GESTOR
log_test "📊 Testing Charts Meta - GESTOR..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X GET "$BASE_URL/charts/meta?user_role=GESTOR" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 4: Charts Meta - CONTROL_GESTION
log_test "📊 Testing Charts Meta - CONTROL_GESTION..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X GET "$BASE_URL/charts/meta?user_role=CONTROL_GESTION" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 5: Charts Options - GESTOR
log_test "🔐 Testing Charts Options - GESTOR..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X GET "$BASE_URL/charts/options/GESTOR" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 6: Charts Options - CONTROL_GESTION
log_test "🔐 Testing Charts Options - CONTROL_GESTION..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X GET "$BASE_URL/charts/options/CONTROL_GESTION" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 7: Charts Pivot - GESTOR (Cambio básico)
log_test "🔄 Testing Charts Pivot - GESTOR..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X POST "$BASE_URL/charts/pivot" \
     -H "Content-Type: application/json" \
     -d '{
       "userid": "gestor-1001-test",
       "message": "cambia a barras horizontales",
       "current_chart_config": {
         "chart_type": "bar",
         "dimension": "periodo",
         "metric": "CONTRATOS"
       },
       "chart_interaction_type": "pivot",
       "user_role": "GESTOR",
       "gestor_id": "1001"
     }' | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 8: Charts Pivot - CONTROL_GESTION
log_test "🔄 Testing Charts Pivot - CONTROL_GESTION..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X POST "$BASE_URL/charts/pivot" \
     -H "Content-Type: application/json" \
     -d '{
       "userid": "admin-control-test",
       "message": "muestra ranking de gestores por margen neto",
       "current_chart_config": {
         "chart_type": "bar",
         "dimension": "producto",
         "metric": "CONTRATOS"
       },
       "chart_interaction_type": "pivot",
       "user_role": "CONTROL_GESTION"
     }' | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 9: Charts Validate Config - GESTOR (Debe ajustar)
log_test "🔍 Testing Charts Validate Config - GESTOR..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X POST "$BASE_URL/charts/validate-config" \
     -H "Content-Type: application/json" \
     -d '{
       "config": {
         "chart_type": "bar",
         "dimension": "gestor",
         "metric": "PRECIO_REAL"
       },
       "user_role": "GESTOR",
       "user_context": {"gestor_id": "1001"}
     }' | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 10: Charts Validate Config - CONTROL_GESTION (Debe pasar)
log_test "🔍 Testing Charts Validate Config - CONTROL_GESTION..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X POST "$BASE_URL/charts/validate-config" \
     -H "Content-Type: application/json" \
     -d '{
       "config": {
         "chart_type": "bar",
         "dimension": "gestor",
         "metric": "PRECIO_REAL"
       },
       "user_role": "CONTROL_GESTION"
     }' | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 11: Charts Create Secure - GESTOR
log_test "🔐 Testing Charts Create Secure - GESTOR..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X POST "$BASE_URL/charts/create-secure" \
     -H "Content-Type: application/json" \
     -d '{
       "data": [
         {"label": "Enero", "value": 100},
         {"label": "Febrero", "value": 120},
         {"label": "Marzo", "value": 95}
       ],
       "config": {
         "chart_type": "line",
         "dimension": "periodo",
         "metric": "CONTRATOS"
       },
       "user_role": "GESTOR",
       "gestor_id": "1001"
     }' | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 12: Integration Classify and Route
log_test "🔀 Testing Integration Classify and Route..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X POST "$BASE_URL/integration/classify-and-route" \
     -H "Content-Type: application/json" \
     -d '{
       "userid": "gestor-1001-test",
       "message": "muéstrame mi evolución de ROE en gráfico de líneas",
       "gestor_id": "1001",
       "include_charts": true
     }' | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 13: Quick Charts
log_test "⚡ Testing Quick Charts..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X GET "$BASE_URL/charts/quick/gestores_ranking" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Test 14: Available Queries
log_test "📋 Testing Available Queries..."
curl -s -w "Status: %{http_code}, Time: %{time_total}s\n" \
     -X GET "$BASE_URL/charts/available-queries" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Resumen final
echo "" | tee -a "$LOG_FILE"
echo "===========================================" | tee -a "$LOG_FILE"
log_test "🎯 Tests cURL completados!"
log_test "📝 Revisa el archivo $LOG_FILE para detalles completos"
log_test "🔍 Busca 'Status: 200' para tests exitosos"
log_test "❌ Busca 'Status: 4xx/5xx' para errores"

# Contar tests exitosos
SUCCESS_COUNT=$(grep -c "Status: 200" "$LOG_FILE")
TOTAL_TESTS=14

echo "" | tee -a "$LOG_FILE"
log_test "📊 Resumen: $SUCCESS_COUNT/$TOTAL_TESTS tests exitosos"

if [ "$SUCCESS_COUNT" -eq "$TOTAL_TESTS" ]; then
    log_test "🎉 ¡TODOS LOS TESTS PASARON!"
    exit 0
else
    log_test "⚠️ Algunos tests fallaron - revisar logs"
    exit 1
fi
