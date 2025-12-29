using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Resido.Database.DBTable
{
    [Table("UserParameter")]
    public class UserParameter
    {
        [Key]
        public Guid Id { get; set; }
        public virtual User User { get; set; }
        public Guid UserId { get; set; }
        public string Key { get; set; }
        public string Value { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }
        public RowStatus RowStatus { get; set; }
    }
    public enum UserParameterKey
    {
        Otp = 0,
        Otp_Send_Time,

        Email_Update_Otp,
        Email_Update_Otp_Send_Time,

        Phone_Update_Otp,
        Phone_Update_Otp_Send_Time,

        Password_Reset_Otp,
        Password_Reset_Otp_Send_Time,

        New_Email_To_Update,
        New_Phone_To_Update,
        New_Dial_Code_To_Update
    }
}
