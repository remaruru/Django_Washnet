import re

path = r'c:\Users\Admin\Downloads\DjangoGroupProjectNew\templates\core\employee\dashboard.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix order.status=='XYZ' to order.status == 'XYZ'
content = re.sub(r"(order\.status)==('[\w_]+')", r"\1 == \2", content)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("Dashboard template fixed.")
