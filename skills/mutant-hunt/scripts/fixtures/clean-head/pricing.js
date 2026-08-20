function total(qty, unit, bulkMin, bulkRate) {
  let price = qty * unit;
  if (qty > bulkMin) {
    price = price * bulkRate;
  }
  if (price < 0) {
    price = 0;
  }
  return price;
}
