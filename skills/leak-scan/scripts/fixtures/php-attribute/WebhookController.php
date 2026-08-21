<?php
namespace Idc\Http;

# The attribute below is DATA, not a comment: PHP 8 attributes open with '#['.
class WebhookController
{
    #[Route("/api/payments/webhook", methods: ["POST"])]
    public function receive(Request $request): Response
    {
        return $this->handler->accept($request);
    }
}
