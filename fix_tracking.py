import sys
import re

with open('c:/Users/Admin/Downloads/DjangoGroupProjectNew/templates/core/customer/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Step 2
content = re.sub(r'class=\"shopee-step \{% if order\.status in \'RIDER_ACCEPTED,PICKED_UP,PROCESSING,READY_FOR_DELIVERY,OUT_FOR_DELIVERY,COMPLETED\' %\}active\{% else %\}inactive\{% endif %\}\"', 
    'class=\"shopee-step {% if order.status in \'RIDER_ACCEPTED,PICKED_UP,AT_SHOP,PROCESSING,READY_FOR_DELIVERY,OUT_FOR_DELIVERY,COMPLETED\' %}active{% else %}inactive{% endif %}\"', content)
    
# Replace Step 3
content = re.sub(r'class=\"shopee-step \{% if order\.status in \'PICKED_UP,PROCESSING,READY_FOR_DELIVERY,OUT_FOR_DELIVERY,COMPLETED\' %\}active\{% else %\}inactive\{% endif %\}\"', 
    'class=\"shopee-step {% if order.status in \'AT_SHOP,PROCESSING,READY_FOR_DELIVERY,OUT_FOR_DELIVERY,COMPLETED\' %}active{% else %}inactive{% endif %}\"', content)

# Replace Text 2
content = re.sub(r'class=\"shopee-text \{% if order\.status in \'RIDER_ACCEPTED,PICKED_UP,PROCESSING,READY_FOR_DELIVERY,OUT_FOR_DELIVERY,COMPLETED\' %\}active\{% else %\}inactive\{% endif %\}\">Accepted', 
    'class=\"shopee-text {% if order.status in \'RIDER_ACCEPTED,PICKED_UP,AT_SHOP,PROCESSING,READY_FOR_DELIVERY,OUT_FOR_DELIVERY,COMPLETED\' %}active{% else %}inactive{% endif %}\">With Rider', content)

# Replace Text 3
content = re.sub(r'class=\"shopee-text \{% if order\.status in \'PICKED_UP,PROCESSING,READY_FOR_DELIVERY,OUT_FOR_DELIVERY,COMPLETED\' %\}active\{% else %\}inactive\{% endif %\}\">With\s+Rider', 
    'class=\"shopee-text {% if order.status in \'AT_SHOP,PROCESSING,READY_FOR_DELIVERY,OUT_FOR_DELIVERY,COMPLETED\' %}active{% else %}inactive{% endif %}\">At Shop', content)

# Progress Line Logic
content = content.replace(
    '''{% elif order.status == 'PICKED_UP' %} width: 40%;
                        {% elif order.status == 'PROCESSING' %} width: 60%;''',
    '''{% elif order.status == 'AT_SHOP' %} width: 40%;
                        {% elif order.status == 'PROCESSING' %} width: 60%;'''
)

with open('c:/Users/Admin/Downloads/DjangoGroupProjectNew/templates/core/customer/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
