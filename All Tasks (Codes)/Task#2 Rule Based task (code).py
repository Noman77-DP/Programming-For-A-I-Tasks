

age = int(input("Enter your age: "))
has_coupon = input("Do you have a coupon? (Yes/No): ")

if age >= 60:
    price = 8.00
    print("Rule: Senior Discount Applied")

if age < 60:
    if age <= 12:
        price = 5.00
        print("Rule: Child Discount Applied")

if age > 12 and age < 60:
    price = 12.00
    print("Rule: Standard Adult Price")

if has_coupon == "Yes":
    final_price = price - 2.00
    print("Rule: Coupon subtracted $2.00")

if has_coupon != "Yes":
    final_price = price
    print("Rule: No coupon used")

print("Please pay:", final_price)