#!/usr/bin/env python3
"""
ChatSphere 部署脚本
支持不同环境的自动化部署
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path


class DeployManager:
    """部署管理器"""
    
    def __init__(self, environment: str):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.valid_environments = ["development", "testing", "production"]
        
        if environment not in self.valid_environments:
            raise ValueError(f"环境必须是: {', '.join(self.valid_environments)}")
    
    def run_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """运行命令"""
        print(f"运行命令: {command}")
        return subprocess.run(command, shell=True, check=check, cwd=self.project_root)
    
    def setup_environment(self):
        """设置环境变量文件"""
        env_file = self.project_root / f".env.{self.environment}"
        target_env = self.project_root / ".env"
        
        if env_file.exists():
            shutil.copy2(env_file, target_env)
            print(f"已复制 {env_file} 到 .env")
        else:
            print(f"警告: 环境文件 {env_file} 不存在")
    
    def check_dependencies(self):
        """检查依赖"""
        print("检查依赖...")
        
        # 检查Docker
        try:
            self.run_command("docker --version")
        except subprocess.CalledProcessError:
            print("错误: Docker 未安装")
            sys.exit(1)
        
        # 检查Docker Compose
        try:
            self.run_command("docker-compose --version")
        except subprocess.CalledProcessError:
            print("错误: Docker Compose 未安装")
            sys.exit(1)
    
    def deploy_development(self):
        """部署开发环境"""
        print("部署开发环境...")
        
        # 启动数据库服务
        self.run_command("docker-compose up -d postgres redis")
        
        # 等待服务启动
        print("等待数据库服务启动...")
        self.run_command("sleep 10")
        
        # 运行数据库迁移
        self.run_command("python scripts/setup.py")
        
        # 启动应用
        print("启动开发服务器...")
        self.run_command("uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    
    def deploy_testing(self):
        """部署测试环境"""
        print("部署测试环境...")
        
        # 启动测试数据库
        self.run_command("docker-compose up -d postgres redis")
        
        # 等待服务启动
        self.run_command("sleep 10")
        
        # 运行测试数据库设置
        self.run_command("python scripts/setup.py --testing")
        
        # 运行测试
        self.run_command("pytest tests/ -v")
    
    def deploy_production(self):
        """部署生产环境"""
        print("部署生产环境...")
        
        # 检查生产环境配置
        self.check_production_config()
        
        # 构建和启动生产服务
        self.run_command("docker-compose -f docker-compose.prod.yml build")
        self.run_command("docker-compose -f docker-compose.prod.yml up -d")
        
        # 等待服务启动
        print("等待服务启动...")
        self.run_command("sleep 30")
        
        # 运行数据库迁移
        self.run_command("docker-compose -f docker-compose.prod.yml exec chatsphere python scripts/setup.py")
        
        # 健康检查
        self.health_check()
    
    def check_production_config(self):
        """检查生产环境配置"""
        required_vars = [
            "SECRET_KEY",
            "POSTGRES_PASSWORD",
            "REDIS_PASSWORD"
        ]
        
        env_file = self.project_root / ".env.production"
        if not env_file.exists():
            print("错误: .env.production 文件不存在")
            sys.exit(1)
        
        with open(env_file) as f:
            content = f.read()
            
        for var in required_vars:
            if f"{var}=your-" in content or f"{var}=password" in content:
                print(f"错误: 生产环境变量 {var} 未正确设置")
                sys.exit(1)
    
    def health_check(self):
        """健康检查"""
        print("执行健康检查...")
        try:
            self.run_command("curl -f http://localhost:8000/health")
            print("✓ 健康检查通过")
        except subprocess.CalledProcessError:
            print("✗ 健康检查失败")
            sys.exit(1)
    
    def stop_services(self):
        """停止服务"""
        print(f"停止 {self.environment} 环境服务...")
        
        if self.environment == "production":
            self.run_command("docker-compose -f docker-compose.prod.yml down")
        else:
            self.run_command("docker-compose down")
    
    def backup_database(self):
        """备份数据库"""
        if self.environment != "production":
            print("只有生产环境支持备份")
            return
        
        print("备份生产数据库...")
        backup_file = f"backup_{self.environment}_{os.strftime('%Y%m%d_%H%M%S')}.sql"
        
        self.run_command(
            f"docker-compose -f docker-compose.prod.yml exec postgres "
            f"pg_dump -U postgres chatsphere > {backup_file}"
        )
        print(f"数据库已备份到: {backup_file}")
    
    def deploy(self):
        """执行部署"""
        print(f"开始部署 {self.environment} 环境...")
        
        # 设置环境
        self.setup_environment()
        
        # 检查依赖
        self.check_dependencies()
        
        # 根据环境执行不同的部署策略
        if self.environment == "development":
            self.deploy_development()
        elif self.environment == "testing":
            self.deploy_testing()
        elif self.environment == "production":
            self.deploy_production()
        
        print(f"✓ {self.environment} 环境部署完成!")


def main():
    parser = argparse.ArgumentParser(description="ChatSphere 部署脚本")
    parser.add_argument(
        "environment",
        choices=["development", "testing", "production"],
        help="部署环境"
    )
    parser.add_argument(
        "--action",
        choices=["deploy", "stop", "backup"],
        default="deploy",
        help="执行的动作"
    )
    
    args = parser.parse_args()
    
    try:
        manager = DeployManager(args.environment)
        
        if args.action == "deploy":
            manager.deploy()
        elif args.action == "stop":
            manager.stop_services()
        elif args.action == "backup":
            manager.backup_database()
            
    except Exception as e:
        print(f"部署失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 