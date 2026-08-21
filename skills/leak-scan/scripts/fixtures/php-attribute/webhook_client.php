<?php
namespace Idc\Client;

class WebhookClient
{
    #[Endpoint("/api/payments/webhook")]
    public function send(array $payload): void
    {
        $this->http->post($payload);
    }
}
