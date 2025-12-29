namespace Resido
{
    public enum LoginOtpDeliveryMethod
    {
        Email,
        Phone
    }
    public enum RowStatus
    {
        Deleted,
        Active,
        DeletedByAdmin
    }
    public enum OtpActionType
    {
        Login_Sms,
        Login_Email,

        Password_Reset_Phone,
        Password_Reset_Email,

        Update_Phone,
        Update_Email,
    }
}
