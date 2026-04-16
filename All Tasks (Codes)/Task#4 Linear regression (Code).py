from sklearn.linear_model import LinearRegression

# Data (study hours vs marks)
A = [[1], [2], [3], [4]]
B = [25, 50, 75, 100]

model = LinearRegression()
model.fit(A, B)

prediction = model.predict([[5], [8], [10]])

print("5 hours:", prediction[0])
print("8 hours:", prediction[1])
print("10 hours:", prediction[2])