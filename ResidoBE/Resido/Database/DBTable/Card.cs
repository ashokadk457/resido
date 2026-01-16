namespace Resido.Database.DBTable
{
    public class Card
    {
        public Guid Id { get; set; }

        // Corresponding int card ID from lock
        public int CardId { get; set; }

        public string CardNumber { get; set; }

        public Guid SmartLockId { get; set; }
        public virtual SmartLock SmartLock { get; set; }
        public DateTime CreatedAt { get; set; }

        public DateTime? UpdatedAt { get; set; }
    }
}
