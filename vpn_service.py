"""
FortiClient VPN 連接服務
使用 openfortivpn 進行 VPN 連接
"""
import subprocess
import time
import os
import signal


class VPNService:
    """VPN 連接管理"""
    
    def __init__(self):
        self.vpn_process = None
        self.host = os.getenv("VPN_HOST", "")  # VPN 伺服器地址，如 vpn.company.com:443
        self.username = os.getenv("VPN_USERNAME", "")
        self.password = os.getenv("VPN_PASSWORD", "")
        self.trusted_cert = os.getenv("VPN_TRUSTED_CERT", "")  # 可選，VPN 伺服器憑證
    
    def is_connected(self) -> bool:
        """檢查 VPN 是否已連接"""
        try:
            # 檢查 ppp0 介面是否存在（openfortivpn 建立的介面）
            result = subprocess.run(
                ["ifconfig", "ppp0"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def connect(self, timeout: int = 30) -> bool:
        """
        連接 VPN
        
        Args:
            timeout: 連接超時時間（秒）
            
        Returns:
            bool: 連接是否成功
        """
        if self.is_connected():
            print("✅ VPN 已經連接")
            return True
        
        if not self.host or not self.username or not self.password:
            print("❌ VPN 設定不完整，請設定環境變數:")
            print("   - VPN_HOST: VPN 伺服器地址 (如 vpn.company.com:443)")
            print("   - VPN_USERNAME: VPN 用戶名")
            print("   - VPN_PASSWORD: VPN 密碼")
            print("   - VPN_TRUSTED_CERT: (可選) VPN 伺服器憑證")
            return False
        
        print(f"🔌 正在連接 VPN: {self.host}...")
        
        try:
            # 建立 openfortivpn 命令
            cmd = [
                "sudo", "openfortivpn",
                self.host,
                "-u", self.username,
                "-p", self.password,
            ]
            
            if self.trusted_cert:
                cmd.extend(["--trusted-cert", self.trusted_cert])
            
            # 在背景執行 VPN 連接
            self.vpn_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 合併 stderr 到 stdout
                text=True
            )
            
            # 等待連接建立，同時收集輸出
            start_time = time.time()
            output_lines = []
            
            while time.time() - start_time < timeout:
                # 檢查是否已連接
                if self.is_connected():
                    print("✅ VPN 連接成功")
                    return True
                
                # 檢查進程是否已結束（失敗）
                poll_result = self.vpn_process.poll()
                if poll_result is not None:
                    # 進程已結束，讀取所有輸出
                    remaining_output = self.vpn_process.stdout.read()
                    if remaining_output:
                        output_lines.extend(remaining_output.strip().split('\n'))
                    
                    self._print_error_details(output_lines, poll_result)
                    self.vpn_process = None
                    return False
                
                # 非阻塞讀取輸出
                try:
                    import select
                    if select.select([self.vpn_process.stdout], [], [], 0.1)[0]:
                        line = self.vpn_process.stdout.readline()
                        if line:
                            line = line.strip()
                            output_lines.append(line)
                            # 即時顯示連接進度
                            if any(keyword in line.lower() for keyword in ['connecting', 'connected', 'tunnel', 'authenticated']):
                                print(f"   {line}")
                except Exception:
                    pass
                
                time.sleep(0.5)
            
            # 超時處理
            print("❌ VPN 連接超時")
            if output_lines:
                print("📋 連接日誌:")
                for line in output_lines[-10:]:  # 顯示最後 10 行
                    print(f"   {line}")
            self.disconnect()
            return False
            
        except FileNotFoundError:
            print("❌ 找不到 openfortivpn，請先安裝:")
            print("   brew install openfortivpn")
            return False
        except PermissionError:
            print("❌ 權限不足，需要設定 sudo 免密碼")
            print("💡 請執行以下步驟:")
            print("   1. 執行: sudo visudo")
            print("   2. 在檔案最後加入:")
            print(f"      {os.getenv('USER', 'your_username')} ALL=(ALL) NOPASSWD: /opt/homebrew/bin/openfortivpn")
            return False
        except Exception as e:
            print(f"❌ VPN 連接失敗: {e}")
            return False
    
    def _print_error_details(self, output_lines: list, exit_code: int):
        """顯示詳細的錯誤訊息"""
        print(f"❌ VPN 連接失敗 (退出碼: {exit_code})")
        
        # 常見錯誤原因對照
        error_hints = {
            "could not connect to gateway": "無法連接到 VPN 伺服器，請檢查 VPN_HOST 是否正確",
            "permission denied": "權限不足，請確保使用 sudo 執行",
            "authentication failed": "認證失敗，請檢查 VPN_USERNAME 和 VPN_PASSWORD",
            "invalid username or password": "帳號或密碼錯誤",
            "certificate": "憑證問題，可能需要設定 VPN_TRUSTED_CERT",
            "timeout": "連接超時，請檢查網路連線",
            "connection refused": "連接被拒絕，VPN 伺服器可能未開啟或端口錯誤",
            "network is unreachable": "網路無法到達，請檢查網路連線",
            "host not found": "找不到主機，請檢查 VPN_HOST 設定",
            "ssl": "SSL/TLS 錯誤，可能是憑證問題",
        }
        
        # 顯示輸出日誌
        if output_lines:
            print("📋 錯誤日誌:")
            for line in output_lines[-15:]:  # 顯示最後 15 行
                print(f"   {line}")
            
            # 分析錯誤原因
            full_output = '\n'.join(output_lines).lower()
            print("\n💡 可能的原因:")
            found_hint = False
            for keyword, hint in error_hints.items():
                if keyword in full_output:
                    print(f"   - {hint}")
                    found_hint = True
            
            if not found_hint:
                print("   - 未知錯誤，請查看上方日誌")
    
    def disconnect(self):
        """斷開 VPN 連接"""
        if self.vpn_process:
            print("🔌 正在斷開 VPN...")
            try:
                # 終止 sudo 進程（會連帶終止 openfortivpn）
                self.vpn_process.terminate()
                self.vpn_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # 如果超時，強制終止
                self.vpn_process.kill()
                self.vpn_process.wait(timeout=5)
            except Exception:
                pass
            self.vpn_process = None
        
        # 等待一下讓網路介面關閉
        time.sleep(1)
        
        if not self.is_connected():
            print("✅ VPN 已斷開")
        else:
            print("⚠️ VPN 可能未完全斷開")
    
    def __enter__(self):
        """Context manager 進入"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 退出"""
        self.disconnect()
        return False


def check_vpn_installed() -> bool:
    """檢查 openfortivpn 是否已安裝"""
    try:
        result = subprocess.run(
            ["which", "openfortivpn"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


if __name__ == "__main__":
    # 測試 VPN 連接
    if not check_vpn_installed():
        print("❌ openfortivpn 未安裝")
        print("💡 安裝方式: brew install openfortivpn")
    else:
        print("✅ openfortivpn 已安裝")
        vpn = VPNService()
        print(f"🔍 VPN 連接狀態: {'已連接' if vpn.is_connected() else '未連接'}")
