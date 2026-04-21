# Import Logistic Regression
from sklearn.linear_model import LogisticRegression

# Training data (Salary in USD)
X = [[20000], [30000], [40000], [50000], [70000], [90000]]

# Output Labels
# 0 = Rejected, 1 = Approved
y = [0, 0, 0, 1, 1, 1]

# Create model
model = LogisticRegression()

# Train model
model.fit(X, y)

# Test input (new salary)
salary = 60000  # you can change this value

# Make prediction
prediction = model.predict([[salary]])

# Show result
if prediction[0] == 1:
    print("Loan: Approved")
else:
    print("Loan: Rejected")