function total(qty, unit, bulkMin, bulkRate) {
  let price = qty * unit;
  if (qty >= bulkMin) {
    price = price * bulkRate;
  }
  return price;
}
