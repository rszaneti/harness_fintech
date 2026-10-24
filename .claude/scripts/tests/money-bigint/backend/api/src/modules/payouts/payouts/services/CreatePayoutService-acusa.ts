export default class CreatePayoutService {
  public execute(amount: string): number {
    return parseFloat(amount) * 100 // @acusa
  }
}
