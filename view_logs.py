#!/usr/bin/env python3
"""
日志查看工具 - 方便查看和分析应用日志
"""
import sys
from pathlib import Path
from datetime import datetime
import pytz

def get_today_log():
    """获取今天的日志文件路径"""
    shanghai_tz = pytz.timezone("Asia/Shanghai")
    today = datetime.now(shanghai_tz).strftime('%Y%m%d')
    log_file = Path("logs") / f"app_{today}.log"
    return log_file

def list_all_logs():
    """列出所有日志文件"""
    log_dir = Path("logs")
    if not log_dir.exists():
        print("❌ 日志目录不存在: logs/")
        return []

    log_files = sorted(log_dir.glob("app_*.log"), reverse=True)
    return log_files

def view_log(log_file, lines=100, level=None):
    """查看日志文件"""
    if not log_file.exists():
        print(f"❌ 日志文件不存在: {log_file}")
        return

    print(f"\n📋 查看日志: {log_file}")
    print(f"{'=' * 80}\n")

    with open(log_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()

        # 过滤日志级别
        if level:
            filtered_lines = [line for line in all_lines if f"[{level}]" in line]
            display_lines = filtered_lines[-lines:] if lines else filtered_lines
        else:
            display_lines = all_lines[-lines:] if lines else all_lines

        for line in display_lines:
            # 添加颜色（可选）
            if "[ERROR]" in line:
                print(f"\033[91m{line.rstrip()}\033[0m")  # 红色
            elif "[WARNING]" in line:
                print(f"\033[93m{line.rstrip()}\033[0m")  # 黄色
            elif "[INFO]" in line:
                print(f"\033[92m{line.rstrip()}\033[0m")  # 绿色
            else:
                print(line.rstrip())

def search_log(log_file, keyword):
    """搜索日志内容"""
    if not log_file.exists():
        print(f"❌ 日志文件不存在: {log_file}")
        return

    print(f"\n🔍 搜索关键词: '{keyword}'")
    print(f"日志文件: {log_file}")
    print(f"{'=' * 80}\n")

    count = 0
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            if keyword.lower() in line.lower():
                count += 1
                # 高亮关键词
                highlighted = line.replace(keyword, f"\033[93m{keyword}\033[0m")
                print(highlighted.rstrip())

    print(f"\n找到 {count} 条匹配记录")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='日志查看工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python view_logs.py                    # 查看今天最近100行日志
  python view_logs.py --lines 50         # 查看今天最近50行日志
  python view_logs.py --all              # 查看今天所有日志
  python view_logs.py --level ERROR      # 只查看错误日志
  python view_logs.py --search "Anthropic"  # 搜索包含 Anthropic 的日志
  python view_logs.py --list             # 列出所有日志文件
        """
    )

    parser.add_argument('--lines', '-n', type=int, default=100,
                      help='显示最后N行日志（默认: 100）')
    parser.add_argument('--all', '-a', action='store_true',
                      help='显示所有日志')
    parser.add_argument('--level', '-l', choices=['INFO', 'WARNING', 'ERROR', 'DEBUG'],
                      help='只显示特定级别的日志')
    parser.add_argument('--search', '-s', type=str,
                      help='搜索包含指定关键词的日志')
    parser.add_argument('--list', action='store_true',
                      help='列出所有日志文件')
    parser.add_argument('--file', '-f', type=str,
                      help='指定日志文件（默认: 今天的日志）')

    args = parser.parse_args()

    # 列出所有日志文件
    if args.list:
        log_files = list_all_logs()
        if not log_files:
            print("📭 没有找到日志文件")
            return

        print("\n📁 日志文件列表:")
        print(f"{'=' * 80}\n")
        for log_file in log_files:
            size = log_file.stat().st_size
            size_kb = size / 1024
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            print(f"📄 {log_file.name:20s} | {size_kb:8.2f} KB | 修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        return

    # 确定日志文件
    if args.file:
        log_file = Path(args.file)
    else:
        log_file = get_today_log()

    # 搜索模式
    if args.search:
        search_log(log_file, args.search)
    else:
        # 查看模式
        lines = None if args.all else args.lines
        view_log(log_file, lines=lines, level=args.level)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
