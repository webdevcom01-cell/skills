def delete_user(id): db.execute(f"DELETE FROM users WHERE id={id}")
