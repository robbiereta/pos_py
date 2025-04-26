import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import styles from '../styles/Home.module.css';

const Home = () => {
  return (
    <div className={styles.container}>
      <Head>
        <title>POS System</title>
        <meta name="description" content="Point of Sale System" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>
          Welcome to POS System
        </h1>

        <div className={styles.grid}>
          <Link href="/sales" className={styles.card}>
            <h2>Sales Management &rarr;</h2>
            <p>Manage sales transactions and view history.</p>
          </Link>
        </div>
      </main>
    </div>
  );
};

export default Home;
