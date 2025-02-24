from web3 import Web3
from eth_account import Account
import time
import os
import sys
import threading

class ZkSyncCLI:
    def __init__(self):
        self.NETWORK_CONFIG = {
            '1': {
                'rpc_url': 'http://localhost:3050',
                'name': 'Local zkSync'
            }
            # More networks can be added here
        }
        self.current_network = None
        self.w3 = None
        self.monitor_thread = None

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_logo(self):
        logo = """
███████╗████████╗ █████╗ ██╗  ██╗██╗
   ███╔╝╚══██╔══╝██╔══██╗╚██╗██╔╝██║
  ███╔╝    ██║   ███████║ ╚███╔╝ ██║
 ███╔╝     ██║   ██╔══██║ ██╔██╗ ██║
███████╗   ██║   ██║  ██║██╔╝ ██╗██║
╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝
                                     
        ZTAXI - Decentralized Ride Platform v1.0
        Powered by zkSync
"""
        print(logo)
        time.sleep(1)

    def select_network(self):
        print("\n=== Available Networks ===")
        for key, network in self.NETWORK_CONFIG.items():
            print(f"{key}. {network['name']}")
        
        while True:
            choice = input("\nSelect network (enter number): ")
            if choice in self.NETWORK_CONFIG:
                self.current_network = choice
                print(f"\n🔄 Connecting to {self.NETWORK_CONFIG[choice]['name']}...")
                if self.connect_network():
                    print(f"\n✅ Successfully connected to {self.NETWORK_CONFIG[choice]['name']}")
                    time.sleep(1)
                    return True
                else:
                    print(f"\n❌ Failed to connect to {self.NETWORK_CONFIG[choice]['name']}")
                    retry = input("\nRetry connection? (y/n): ")
                    if retry.lower() != 'y':
                        return False
            else:
                print("\n❌ Invalid selection, please try again!")

    def connect_network(self):
        """Initialize web3 connection"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.NETWORK_CONFIG[self.current_network]['rpc_url']))
            if self.w3.is_connected():
                # Start network monitoring
                if self.monitor_thread is None:
                    self.monitor_thread = threading.Thread(target=self.monitor_connection, daemon=True)
                    self.monitor_thread.start()
                return True
            return False
        except Exception as e:
            print(f"\n❌ Connection error: {str(e)}")
            return False

    def monitor_connection(self):
        """Monitor network connection every 30 seconds"""
        while True:
            if not self.w3.is_connected():
                print("\n⚠️ Network connection lost. Attempting to reconnect...")
                self.connect_network()
            time.sleep(30)

    def show_menu(self):
        menu = """
Please select an operation:
1. Check Account Balance
2. Transfer ETH
3. Exit

Enter your choice (1-3): """
        return input(menu)

    def check_balance(self):
        self.clear_screen()
        print("\n=== Check Account Balance ===")
        print("\nFormat: 0x... (42 characters hexadecimal address)")
        address = input("\nEnter wallet address: ")
        
        try:
            if not self.w3.is_address(address):
                print("❌ Invalid wallet address!")
                return
            
            balance = self.w3.eth.get_balance(address)
            balance_eth = self.w3.from_wei(balance, 'ether')
            print(f"\n💰 Balance: {balance_eth} ETH")
        except Exception as e:
            print(f"❌ Query failed: {str(e)}")
        
        input("\nPress Enter to return to main menu...")

    def transfer(self):
        self.clear_screen()
        print("\n=== Transfer ETH ===")
        
        try:
            print("\nPrivate Key Format: 0x... or without 0x (64 characters hexadecimal)")
            from_private_key = input("Enter sender's private key: ")
            
            print("\nAddress Format: 0x... (42 characters hexadecimal address)")
            to_address = input("Enter recipient's address: ")
            
            print("\nAmount Format: e.g., 0.1 (decimal number)")
            amount = float(input("Enter amount in ETH: "))

            if not self.w3.is_address(to_address):
                print("❌ Invalid recipient address!")
                return

            account = Account.from_key(from_private_key)
            from_address = account.address

            amount_wei = self.w3.to_wei(amount, 'ether')
            
            # 构建初始交易对象
            transaction = {
                'from': from_address,
                'to': to_address,
                'value': amount_wei,
                'nonce': self.w3.eth.get_transaction_count(from_address),
            }
            
            # 预估gas
            try:
                estimated_gas = self.w3.eth.estimate_gas(transaction)
                # zkSync通常需要更多的gas，增加20%作为缓冲
                gas_limit = int(estimated_gas * 1.2)
            except Exception as e:
                print(f"⚠️ Gas estimation failed, using default gas limit")
                gas_limit = 3000000  # 设置一个较大的默认值

            # 获取当前gas价格
            gas_price = self.w3.eth.gas_price
            
            # 更新交易对象
            transaction.update({
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': self.w3.eth.chain_id
            })

            # 显示gas信息
            estimated_gas_cost = gas_limit * gas_price
            estimated_gas_eth = self.w3.from_wei(estimated_gas_cost, 'ether')
            print(f"\n⛽ Estimated gas cost: {estimated_gas_eth} ETH")

            print("\n📝 Transaction Details:")
            print(f"From: {from_address}")
            print(f"To: {to_address}")
            print(f"Amount: {amount} ETH")
            print(f"Gas Limit: {gas_limit}")
            print(f"Gas Price: {self.w3.from_wei(gas_price, 'gwei')} Gwei")
            
            confirm = input("\nConfirm transaction? (y/n): ")
            if confirm.lower() != 'y':
                print("Transaction cancelled")
                return

            signed_txn = self.w3.eth.account.sign_transaction(transaction, from_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            print("\n⏳ Transaction sent, waiting for confirmation...")
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"\n✅ Transaction completed!")
            print(f"📜 Transaction hash: {tx_receipt['transactionHash'].hex()}")

        except Exception as e:
            print(f"\n❌ Transfer failed: {str(e)}")
        
        input("\nPress Enter to return to main menu...")

    def run(self):
        self.clear_screen()
        self.show_logo()
        
        # Select and connect to network first
        if not self.select_network():
            print("\n❌ Cannot proceed without network connection. Exiting...")
            return

        while True:
            self.clear_screen()
            choice = self.show_menu()
            
            if choice == '1':
                self.check_balance()
            elif choice == '2':
                self.transfer()
            elif choice == '3':
                print("\n👋 Thank you for using ZTAXI! Goodbye!")
                break
            else:
                print("\n❌ Invalid option, please try again!")
                time.sleep(1)

def main():
    try:
        cli = ZkSyncCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Program interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Program error: {str(e)}")

if __name__ == "__main__":
    main()