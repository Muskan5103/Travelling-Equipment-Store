from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_invoice(order, order_items, file_path):
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "INVOICE")

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, f"Order ID: {order.id}")
    c.drawString(50, height - 100, f"Customer: {order.user.username}")
    c.drawString(50, height - 120, f"Address: {order.address}")

    y = height - 170
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Product")
    c.drawString(250, y, "Qty")
    c.drawString(300, y, "Price")

    c.setFont("Helvetica", 10)
    y -= 20

    for item in order_items:
        c.drawString(50, y, item.variant.product.name)
        c.drawString(250, y, str(item.quantity))
        c.drawString(300, y, f"₹ {item.price}")
        y -= 20

    c.drawString(50, y - 20, f"Total Amount: ₹ {order.total_amount}")
    c.showPage()
    c.save()
