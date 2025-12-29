namespace Resido
{/// <summary>
 /// Defines the method of adding a custom passcode.
 /// </summary>
    public enum AddType
    {
        /// <summary>
        /// Add via phone Bluetooth.
        /// Requires calling APP SDK method to add passcode first, then sync to cloud.
        /// </summary>
        Bluetooth = 1,

        /// <summary>
        /// Add via gateway or WiFi lock.
        /// Can be called directly if lock is WiFi or connected to gateway.
        /// </summary>
        Cloud = 2
    }

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
