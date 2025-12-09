# Bu script YEREL bilgisayarda çalışıp, çıktıları VDS'e gönderecek.
# This script runs on LOCAL machine, sending logs to VDS.

$VDS_IP = "45.43.154.16"
$LOG_PATH = "C:\Users\Administrator\.gemini\RemoteLogs\build.log"

Write-Host "--- Hibrid Derleme Başlatılıyor ---" -ForegroundColor Cyan
Write-Host "Hedef: $VDS_IP"

# 0. Log Dosyasını Temizle (Yeni Oturum)
Invoke-Command -ComputerName $VDS_IP -ScriptBlock { Clear-Content "C:\Users\Administrator\.gemini\RemoteLogs\build.log" } 2>$null
if (-not $?) {
    # SSH Fallback if WinRM not configured or fail
    ssh Administrator@$VDS_IP "powershell -Command \"Set-Content -Path 'C:\Users\Administrator\.gemini\RemoteLogs\build.log' -Value ''\""
}

# 1. Derleme Komutu (Burayı kullandığınız dile göre değiştireceğiz, örn: 'pio run', 'arduino-cli compile')
# Şimdilik simülasyon yapıyoruz:
$BuildCommand = {
    Write-Host "Derleme islemi simule ediliyor..."
    Start-Sleep -Seconds 1
    Write-Host "Kütüphaneler taranıyor..."
    Start-Sleep -Seconds 1
    Write-Host "HATA YOK. Derleme Başarılı!" -ForegroundColor Green
    # Hata simülasyonu için üst satırı silip şunu açabilirsiniz:
    # Write-Error "Syntax Error: main.c line 42; missing ';'"
}

# 2. Komutu Çalıştır ve Çıktıyı Hem Ekrana Hem VDS'e Bas
# Tee-Object kullanabilirdik ama SSH'a pipe etmek daha garanti.
try {
    Invoke-Command -ScriptBlock $BuildCommand | ForEach-Object {
        $line = $_
        Write-Output $line # Yerel Ekrana Yaz
        # VDS'e Gönder (Append Mode)
        $line | ssh Administrator@$VDS_IP "Add-Content '$LOG_PATH'" 2>$null
    }
}
catch {
    Write-Error "Bir hata oluştu: $_"
    $_ | ssh Administrator@$VDS_IP "Add-Content '$LOG_PATH'" 2>$null
}

Write-Host "--- İşlem Tamamlandı ---" -ForegroundColor Cyan
