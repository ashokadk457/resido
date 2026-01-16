using Resido.Helper;

namespace Resido.Database.DBTable
{
    public class EKey
    {
        public Guid Id { get; set; }

        // Corresponding int ID from lock system
        public int EKeyId { get; set; }

        public string KeyName { get; set; }

        public Guid SmartLockId { get; set; }
        public virtual SmartLock SmartLock { get; set; }

        public DateTime CreatedAt { get; set; } = DateTimeHelper.GetUtcTime();

        public DateTime? UpdatedAt { get; set; }
    }
}
