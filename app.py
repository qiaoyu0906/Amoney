from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 设置一个 secret key 用于 session 加密


def calculate_settlements(people): 
    # 计算每个人的差额，正值表示收款，负值表示付款
    balances = {name: balance for name, balance in people.items()}

    # 分成两组：收款人和付款人
    payers = {name: -balance for name, balance in balances.items() if balance < 0}  # 欠钱的人，余额为负
    receivers = {name: balance for name, balance in balances.items() if balance > 0}  # 该收钱的人，余额为正

    # 开始结算
    settlements = []

    while payers and receivers:
        payer_name, payer_amount = payers.popitem()  # 获取一个付款人
        receiver_name, receiver_amount = receivers.popitem()  # 获取一个收款人

        # 付款人需要支付的金额是 50 元，收款人应收金额是 30 元，则支付 30 元。
        transfer_amount = min(payer_amount, receiver_amount)

        settlements.append(f"{payer_name} 要支付 {receiver_name} {transfer_amount:.2f} 元")

        # 更新付款人和收款人的余额
        payer_amount -= transfer_amount
        receiver_amount -= transfer_amount

        # 如果付款人还有剩余未付款的部分，放回 payers
        if payer_amount > 0:
            payers[payer_name] = payer_amount

        # 如果收款人还有剩余未收的钱，放回 receivers
        if receiver_amount > 0:
            receivers[receiver_name] = receiver_amount

    return settlements

@app.route("/", methods=["GET", "POST"])
def add_participants():
    if request.method == "POST":
        # 获取用户输入的参与者名字
        participants = request.form.get("participants").split()
        session['participants'] = participants  # 将参与者保存到 session
        return redirect(url_for("index"))  # 不再需要通过 URL 参数传递
    
    return render_template("add_participants.html")

@app.route("/form", methods=["GET", "POST"])
def index():
    # 从 session 中获取参与者名字
    participants = session.get('participants', [])
    if not participants:
        return redirect(url_for('add_participants'))  # 如果没有参与者信息，重定向到添加页面
    
    people = {person: 0 for person in participants}  # 初始化每个人的余额
    
    if request.method == "POST":
        receipts_data = []
        receipt_index = 1

        # 动态处理所有小票
        while True:
            total_amount = request.form.get(f"total_amount_{receipt_index}")
            if not total_amount:
                break  # 没有更多小票了

            total_amount = float(total_amount)  # 获取总金额
            selected_people = request.form.getlist(f"participants_{receipt_index}")  # 获取参与平摊的人
            payer = request.form.get(f"payer_{receipt_index}")  # 获取付款人

            # 更新付款人的balance，增加小票总金额
            people[payer] += total_amount

            # 处理个人消费
            total_personal_expense = 0
            personal_expenses = {}

            for person in selected_people:
                # 从表单中获取个人消费，如果未填写则默认为0
                personal_expense_value = request.form.get(f"personal_expense_{person}_{receipt_index}", "0")
                try:
                    personal_expense = eval(personal_expense_value)  # 计算个人消费的值
                except:
                    personal_expense = 0  # 如果输入无效，则默认消费为0

                personal_expenses[person] = personal_expense
                total_personal_expense += personal_expense

                # 更新个人的balance，减去个人消费金额
                people[person] -= personal_expense

            # 计算每个人的平摊金额
            remaining_amount = total_amount - total_personal_expense
            if selected_people:
                share_per_person = remaining_amount / len(selected_people)
            else:
                share_per_person = 0

            # 平摊的每个人balance减去平摊金额
            for person in selected_people:
                people[person] -= share_per_person

            # 保存该小票的结果
            receipts_data.append({
                "receipt_index": receipt_index,
                "selected_people": selected_people,
                "payer": payer,
                "total_personal_expense": total_personal_expense,
                "share_per_person": share_per_person,
                "personal_expenses": personal_expenses
            })

            receipt_index += 1
        
        # 计算最终的结算
        settlements = calculate_settlements(people)

        # 返回模板并显示结果
        return render_template("result.html", receipts_data=receipts_data, people=people, settlements=settlements)

    return render_template("index.html", people=people)


if __name__ == "__main__":
    app.run(debug=True)
