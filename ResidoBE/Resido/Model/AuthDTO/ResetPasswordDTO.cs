namespace Resido.Model.AuthDTO
{
    public class ResetPasswordDTO: CreatePasswordDTO
    {
        public string Otp { get; set; }
    }
}
