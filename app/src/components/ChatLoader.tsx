import styles from "./ChatLoader.module.css";

const ChatLoader = () => {
  return (
    <div className={styles.ChatLoader}>
      <span className={styles.dot}>.</span>
      <span className={styles.dot}>.</span>
      <span className={styles.dot}>.</span>
    </div>
  );
};

export default ChatLoader;