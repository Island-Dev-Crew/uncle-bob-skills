=begin
The wire header "X-Idc-Signature" and the 300 second skew ceiling are owned by
WebhookContract. This block only explains them; restating a fact in prose must
never make prose a site.
=end
def sign(digest)
  { WebhookContract::SIGNATURE_HEADER => digest }
end
