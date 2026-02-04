import { intentRequest } from './intents';

export async function postChatterMessage(params: {
  model: string;
  res_id: number;
  body: string;
  subject?: string;
}) {
  return intentRequest<{ result: { message_id: number } }>({
    intent: 'chatter.post',
    params: {
      model: params.model,
      res_id: params.res_id,
      body: params.body,
      subject: params.subject,
    },
  });
}
