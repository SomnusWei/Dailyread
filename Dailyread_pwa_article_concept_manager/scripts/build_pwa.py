import subprocess
import os

os.chdir(r'e:\item\DailyRead\Dailyread_pwa_article_concept_manager')

npm_cmd = r'C:\Program Files\nodejs\npm.cmd'

print('安装 html2pdf.js...')
result = subprocess.run([npm_cmd, 'install', 'html2pdf.js'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print('STDERR:', result.stderr)

print('\n构建项目...')
result = subprocess.run([npm_cmd, 'run', 'build'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print('STDERR:', result.stderr)

print('\n完成！')
