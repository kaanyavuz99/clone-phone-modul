# Windows Client Bridge Script (Persistent Tunnel)

$VDS_IP = "45.43.154.16"
$LOG_PATH = "C:\Users\Administrator\.gemini\RemoteLogs\build.log"

Write-Host "--- Hibrid Derleme & Monitor (Persistent Tunnel) ---" -ForegroundColor Cyan
Write-Host "Hedef: $VDS_IP"

# 0. Logları Temizle
ssh Administrator@$VDS_IP "powershell -Command \"Set-Content -Path '$LOG_PATH' -Value ''\""

# 1. Derleme Komutu
# Gerçek ortamda burası: pio run -t upload; pio device monitor
# Simülasyon veya gerçek komut:
$BuildBlock = {
    # PlatformIO komutları burada çalışacak
    # Write-Host "Starting PIO..."
    cmd /c "pio run -t upload && pio device monitor"
}

# 2. Çalıştır ve Tünelle
# PowerShell'de stream yönetimi biraz farklıdır.
# Komutun çıktısını anlık (Stream) olarak alıp hem ekrana (Host) hem SSH'a (Remote) basacağız.

try {    
    # Invoke-Command yerine doğrudan Call operator & kullanıyoruz stream için
    & $BuildBlock | Tee-Object -Variable OutputLog | Out-Host
    
    # Not: PowerShell'de tam eşzamanlı "tee" linux'taki gibi kolay değildir.
    # Yukarıdaki komut önce ekrana basar, sonra variable'a atar (bufferlanır).
    # Gerçek eşzamanlılık için aşağıdakini yapıyoruz:
    
    # REVISED STRATEGY:
    # 3. Yöntem: Object Event Action (Daha karmaşık ama gerçek zamanlı)
    # Basitlik için: Doğrudan SSH process'ine pipe ediyoruz, ama SSH process'i 
    # ekrana çıktı veremeyebilir.
    
    # En basit ve sağlam yöntem (Linux mantığına yakın):
    # Komutu çalıştır, çıktıyı al, hem Write-Host yap hem SSH'a stdin'den gönder.
    
    cmd /c "pio run -t upload && pio device monitor" 2>&1 | ForEach-Object {
        $line = $_
        Write-Host $line
        $line | ssh Administrator@$VDS_IP "cmd /c type CON >> ""$LOG_PATH"""
        # Windows'ta her satır için SSH açmak maalesef kaçınılmaz olabilir pipe syntax'ı olmadan.
        # Ancak "cmd /c ... | ssh" yapabiliriz:
    }
}
catch {
    Write-Error "Hata: $_"
}

# NOTE for User: Windows'ta tam stream pipe için en iyisi WSL kullanmaktır.
# Bu script 'Line-by-Line' çalışmaya devam edecek (Windows kısıtlamaları yüzünden komplike)
# Ama ZorinOS kullandığınız için Linux scripti (build_bridge.sh) mükemmel çalışacaktır.
