# TQSdk 学习示例代码 - 带回测功能的双均线策略
from datetime import date
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask
from tqsdk.exceptions import BacktestFinished

def main():
    # 1. 初始化API连接 (使用回测模式)
    api = TqApi(
        backtest=TqBacktest(
            start_dt=date(2023, 10, 1),  # 回测开始日期
            end_dt=date(2023, 12, 31)   # 回测结束日期
        ),
        web_gui=True,  # 开启图形化界面
        auth=TqAuth("QiZhihui", "QZH123"),  # 您的账号
    )
    
    try:
        # 2. 获取螺纹钢主力合约行情
        symbol = "SHFE.rb2401"  # 合约代码可能需要根据实际情况调整
        quote = api.get_quote(symbol)
        print(f"获取{symbol}行情数据...")

        # 3. 获取K线数据 (15分钟线)
        klines = api.get_kline_serial(symbol, 15*60, data_length=50)
        print(f"已获取{len(klines)}根K线数据")

        # 4. 创建目标持仓任务
        target_pos = TargetPosTask(api, symbol)

        # 初始化变量记录上一次的均线状态
        last_ma5 = None
        last_ma20 = None

        # 5. 改进版双均线策略
        try:
            while True:
                api.wait_update()
                if api.is_changing(klines):
                    # 计算5日和20日均线
                    ma5 = klines.close.iloc[-5:].mean()
                    ma20 = klines.close.iloc[-20:].mean()
                    
                    # 交易信号判断（只在真正的金叉/死叉时触发）
                    if last_ma5 is not None and last_ma20 is not None:
                        # 金叉条件：前一根K线MA5 <= MA20，当前K线MA5 > MA20
                        if last_ma5 <= last_ma20 and ma5 > ma20:
                            print(f"最新价: {quote.last_price}: 金叉信号: MA5({ma5:.2f})上穿MA20({ma20:.2f})，做多1手")
                            target_pos.set_target_volume(1)
                            
                        
                        # 死叉条件：前一根K线MA5 >= MA20，当前K线MA5 < MA20
                        elif last_ma5 >= last_ma20 and ma5 < ma20:
                            print(f"最新价: {quote.last_price}: 死叉信号: MA5({ma5:.2f})下穿MA20({ma20:.2f})，做空1手")
                            target_pos.set_target_volume(-1)
                            
                    
                    # 保存当前均线值供下次比较
                    last_ma5 = ma5
                    last_ma20 = ma20
                            
        except BacktestFinished:
            print("---------- 回测正常结束 ----------")

    finally:
        # 6. 关闭API连接
        api.close()
        print("API连接已关闭")

if __name__ == "__main__":
    main()
